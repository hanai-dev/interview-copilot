"""Windows audio capture: your microphone + whatever the PC is playing (WASAPI loopback).

Output is a single stereo 16 kHz 16-bit PCM stream:
    left  channel (0) = microphone      -> "Me"
    right channel (1) = speaker output  -> "Interviewer"

Keeping the two sources on separate channels is what makes speaker labeling reliable:
Deepgram transcribes each channel independently, so we always know who said what.
"""
from __future__ import annotations

import math
import threading
import time
import wave
from pathlib import Path
from typing import Callable, Optional

import numpy as np

TARGET_RATE = 16000
TICK_S = 0.02          # mixer wakes every 20 ms
JITTER_DELAY_S = 0.10  # hold 100 ms of audio so uneven device callbacks don't cause gaps
MAX_BACKLOG_S = 0.50   # if a device runs ahead by more than this, drop the excess (keeps latency low)
LEVEL_EVERY_S = 0.1


class AudioUnavailable(RuntimeError):
    pass


def _pyaudio():
    try:
        import pyaudiowpatch as pyaudio  # type: ignore
    except ImportError as e:
        raise AudioUnavailable(
            "Audio capture needs Windows and the PyAudioWPatch package "
            "(it installs automatically from requirements.txt on Windows). "
            "On other systems you can still try Demo mode."
        ) from e
    return pyaudio


def list_devices() -> dict:
    """Microphones and speaker outputs (as loopback inputs) on the WASAPI host API."""
    pyaudio = _pyaudio()
    p = pyaudio.PyAudio()
    try:
        wasapi = p.get_host_api_info_by_type(pyaudio.paWASAPI)
        default_in = wasapi.get("defaultInputDevice", -1)
        default_out = wasapi.get("defaultOutputDevice", -1)
        default_out_name = p.get_device_info_by_index(default_out)["name"] if default_out >= 0 else ""
        mics, speakers = [], []
        for i in range(p.get_device_count()):
            d = p.get_device_info_by_index(i)
            if d.get("hostApi") != wasapi["index"]:
                continue
            if d.get("isLoopbackDevice"):
                name = d["name"].replace(" [Loopback]", "")
                speakers.append({"index": i, "name": name,
                                 "default": bool(default_out_name) and default_out_name in d["name"]})
            elif d.get("maxInputChannels", 0) > 0:
                mics.append({"index": i, "name": d["name"], "default": i == default_in})
        return {"mics": mics, "speakers": speakers}
    finally:
        p.terminate()


def _linear_resampler(in_rate: int):
    ratio = TARGET_RATE / in_rate

    def resample(x: np.ndarray) -> np.ndarray:
        n_out = int(round(len(x) * ratio))
        if n_out <= 0 or len(x) == 0:
            return np.zeros(0, np.float32)
        xp = np.linspace(0, len(x) - 1, n_out)
        return np.interp(xp, np.arange(len(x)), x).astype(np.float32)

    return resample


class _Source:
    """One input device: downmix to mono, resample to 16 kHz, buffer."""

    def __init__(self, in_rate: int, in_channels: int):
        self.in_channels = max(1, in_channels)
        if in_rate == TARGET_RATE:
            self._resample = lambda x: x
        else:
            try:
                import soxr
                stream = soxr.ResampleStream(in_rate, TARGET_RATE, 1, dtype="float32")
                self._resample = stream.resample_chunk
            except Exception:
                self._resample = _linear_resampler(in_rate)
        self._buf = np.zeros(0, np.float32)
        self._lock = threading.Lock()

    def push(self, raw: bytes) -> None:
        a = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
        if self.in_channels > 1:
            usable = len(a) - len(a) % self.in_channels
            a = a[:usable].reshape(-1, self.in_channels).mean(axis=1)
        y = np.asarray(self._resample(a), dtype=np.float32)
        with self._lock:
            self._buf = np.concatenate([self._buf, y])

    def take(self, n: int) -> np.ndarray:
        with self._lock:
            max_backlog = int(MAX_BACKLOG_S * TARGET_RATE)
            if len(self._buf) > n + max_backlog:
                self._buf = self._buf[-(n + int(JITTER_DELAY_S * TARGET_RATE)):]
            out, self._buf = self._buf[:n], self._buf[n:]
        if len(out) < n:  # loopback sends nothing while the PC is silent -> pad with silence
            out = np.concatenate([out, np.zeros(n - len(out), np.float32)])
        return out


def _level(x: np.ndarray) -> float:
    rms = float(np.sqrt(np.mean(x * x))) if len(x) else 0.0
    db = 20 * math.log10(rms + 1e-9)
    return max(0.0, min(1.0, (db + 60) / 60))


def _to_int16(x: np.ndarray) -> np.ndarray:
    return (np.clip(x, -1.0, 1.0) * 32767).astype(np.int16)


class DualCapture:
    """Captures mic + speaker loopback and emits interleaved stereo frames."""

    def __init__(
        self,
        on_frame: Callable[[bytes], None],
        on_levels: Optional[Callable[[float, float], None]] = None,
        mic_index: Optional[int] = None,
        speaker_index: Optional[int] = None,
        wav_path: Optional[Path] = None,
    ):
        self.on_frame = on_frame
        self.on_levels = on_levels
        self.mic_index = mic_index
        self.speaker_index = speaker_index
        self.wav_path = wav_path
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._p = None
        self._streams = []
        self._wav = None
        self.mic_name = ""
        self.speaker_name = ""

    # -- device lookup -------------------------------------------------
    def _resolve(self, pyaudio):
        p = self._p
        wasapi = p.get_host_api_info_by_type(pyaudio.paWASAPI)

        if self.mic_index is not None:
            mic = p.get_device_info_by_index(self.mic_index)
        else:
            idx = wasapi.get("defaultInputDevice", -1)
            mic = p.get_device_info_by_index(idx) if idx >= 0 else p.get_default_input_device_info()

        if self.speaker_index is not None:
            spk = p.get_device_info_by_index(self.speaker_index)
        else:
            spk = None
            try:
                spk = p.get_default_wasapi_loopback()
            except Exception:
                out = p.get_device_info_by_index(wasapi["defaultOutputDevice"])
                for lb in p.get_loopback_device_info_generator():
                    if out["name"] in lb["name"]:
                        spk = lb
                        break
            if spk is None:
                raise AudioUnavailable("Couldn't find a loopback device for your speakers/headphones.")
        return mic, spk

    def _open(self, pyaudio, info: dict, source: _Source):
        rate = int(info["defaultSampleRate"])

        def callback(in_data, frame_count, time_info, status):
            if in_data:
                source.push(in_data)
            return (None, pyaudio.paContinue)

        return self._p.open(
            format=pyaudio.paInt16,
            channels=source.in_channels,
            rate=rate,
            input=True,
            input_device_index=info["index"],
            frames_per_buffer=max(256, int(rate * 0.02)),
            stream_callback=callback,
        )

    # -- lifecycle -----------------------------------------------------
    def start(self) -> None:
        pyaudio = _pyaudio()
        self._p = pyaudio.PyAudio()
        try:
            mic, spk = self._resolve(pyaudio)
            self.mic_name = mic["name"]
            self.speaker_name = spk["name"].replace(" [Loopback]", "")
            self._mic = _Source(int(mic["defaultSampleRate"]), int(mic["maxInputChannels"]))
            self._spk = _Source(int(spk["defaultSampleRate"]), int(spk["maxInputChannels"]))
            self._streams = [self._open(pyaudio, mic, self._mic), self._open(pyaudio, spk, self._spk)]
            for s in self._streams:
                s.start_stream()
        except AudioUnavailable:
            self.stop()
            raise
        except Exception as e:
            self.stop()
            raise AudioUnavailable(f"Couldn't open audio devices: {e}") from e

        if self.wav_path:
            self.wav_path.parent.mkdir(parents=True, exist_ok=True)
            self._wav = wave.open(str(self.wav_path), "wb")
            self._wav.setnchannels(2)
            self._wav.setsampwidth(2)
            self._wav.setframerate(TARGET_RATE)

        self._stop.clear()
        self._thread = threading.Thread(target=self._mix_loop, name="audio-mixer", daemon=True)
        self._thread.start()

    def _mix_loop(self) -> None:
        t0 = time.perf_counter()
        emitted = 0
        last_level = 0.0
        while not self._stop.is_set():
            time.sleep(TICK_S)
            now = time.perf_counter()
            due = int((now - t0 - JITTER_DELAY_S) * TARGET_RATE) - emitted
            if due < TARGET_RATE // 100:  # wait for at least 10 ms
                continue
            me = self._mic.take(due)
            them = self._spk.take(due)
            emitted += due

            stereo = np.empty(due * 2, dtype=np.int16)
            stereo[0::2] = _to_int16(me)
            stereo[1::2] = _to_int16(them)
            data = stereo.tobytes()
            try:
                self.on_frame(data)
            except Exception:
                pass
            if self._wav:
                self._wav.writeframes(data)
            if self.on_levels and now - last_level >= LEVEL_EVERY_S:
                last_level = now
                try:
                    self.on_levels(_level(me), _level(them))
                except Exception:
                    pass

    def stop(self) -> None:
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        for s in self._streams:
            try:
                s.stop_stream()
                s.close()
            except Exception:
                pass
        self._streams = []
        if self._p:
            try:
                self._p.terminate()
            except Exception:
                pass
            self._p = None
        if self._wav:
            try:
                self._wav.close()
            except Exception:
                pass
            self._wav = None
