"""Audio capture: your microphone + whatever the computer is playing.

Windows on x64 uses PyAudioWPatch (WASAPI loopback). Everywhere else (macOS, Linux, Windows on ARM)
uses SoundCard: loopback on Windows, the speakers' "monitor" on Linux (PulseAudio/PipeWire). A Mac
can't record its own output, so there the call audio comes from a virtual device such as BlackHole.

Output is a single stereo 16 kHz 16-bit PCM stream:
    left  channel (0) = microphone      -> "Me"
    right channel (1) = speaker output  -> "Interviewer"

Keeping the two sources on separate channels is what makes speaker labeling reliable:
Deepgram transcribes each channel independently, so we always know who said what.
"""
from __future__ import annotations

import math
import sys
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
SC_BLOCK = TARGET_RATE // 50  # SoundCard reads 20 ms at a time
VIRTUAL = ("blackhole", "loopback", "soundflower")  # Mac virtual devices that carry the call audio


class AudioUnavailable(RuntimeError):
    pass


def _backend():
    """(pyaudiowpatch, None) where it installs (Windows x64, the most tested path), else (None, soundcard)."""
    try:
        import pyaudiowpatch as pyaudio  # type: ignore
        return pyaudio, None
    except ImportError:
        pass
    try:
        import soundcard  # type: ignore
    except Exception as e:  # Linux without PulseAudio/PipeWire fails here
        raise AudioUnavailable(
            "Audio capture needs the packages in requirements.txt (run.bat or run.command installs them) and, "
            f"on Linux, PulseAudio or PipeWire. You can still try Demo mode. ({str(e) or type(e).__name__})"
        ) from e
    return None, soundcard


def list_devices() -> dict:
    pyaudio, sc = _backend()
    return _sc_list(sc) if sc else _pa_list(pyaudio)


def _sc_inputs(sc):
    """Every input, numbered by position. Loopbacks are the speakers; a Mac has none, so any input can be the call."""
    devs = sc.all_microphones(include_loopback=True)
    mics = [i for i, d in enumerate(devs) if not d.isloopback]
    return devs, mics, [i for i, d in enumerate(devs) if d.isloopback] or mics


def _sc_defaults(sc, devs, mics, spks):
    """(mic, call audio) positions: the system mic, and the loopback of the system output (or BlackHole on a Mac)."""
    def find(cands, ok):
        return next((i for i in cands if ok(devs[i])), None)

    try:
        mic_id = sc.default_microphone().id
    except Exception:
        mic_id = None
    try:
        out = sc.default_speaker().name
    except Exception:
        out = ""
    virtual = lambda d: any(v in d.name.lower() for v in VIRTUAL)
    mic = find(mics, lambda d: d.id == mic_id and not virtual(d))  # BlackHole as system input is still the call
    if mic is None:
        mic = find(mics, lambda d: not virtual(d))
    spk = find(spks, lambda d: d.isloopback and bool(out) and out in d.name)  # Linux: "Monitor of <out>"
    if spk is None:
        spk = find(spks, lambda d: d.isloopback or virtual(d))
    return mic, spk


def _sc_list(sc) -> dict:
    devs, mics, spks = _sc_inputs(sc)
    dmic, dspk = _sc_defaults(sc, devs, mics, spks)
    row = lambda i, default: {"index": i, "name": devs[i].name, "default": i == default}
    return {"mics": [row(i, dmic) for i in mics], "speakers": [row(i, dspk) for i in spks]}


def _no_call_audio() -> str:
    if sys.platform == "darwin":
        return ("A Mac can't record what it plays by itself. Install the free BlackHole 2ch driver, make a "
                "Multi-Output Device (your headphones + BlackHole) in Audio MIDI Setup and use it as your "
                "sound output, then pick BlackHole under Settings > Call audio.")
    return "Couldn't find a loopback (monitor) of your speakers/headphones."


def _sd_input(name: str, source: "_Source"):
    """The same Windows mic through PortAudio (sounddevice), converted to 16 kHz mono by WASAPI."""
    import sounddevice as sd  # type: ignore
    sd._terminate()  # sounddevice lists devices once per process; refresh so a headset plugged in later is found
    sd._initialize()
    wasapi = next(i for i, h in enumerate(sd.query_hostapis()) if "WASAPI" in h["name"])
    index = next(i for i, d in enumerate(sd.query_devices())
                 if d["hostapi"] == wasapi and d["max_input_channels"] > 0 and d["name"] == name)
    stream = sd.InputStream(device=index, samplerate=TARGET_RATE, channels=1, dtype="float32", blocksize=SC_BLOCK,
                            extra_settings=sd.WasapiSettings(auto_convert=True),
                            callback=lambda data, frames, t, status: source.push_mono(data[:, 0].copy()))
    stream.start()
    return stream


def _pa_list(pyaudio) -> dict:
    """Microphones and speaker outputs (as loopback inputs) on the WASAPI host API."""
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
        self.push_mono(a)

    def push_mono(self, a: np.ndarray) -> None:
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
        self._readers = []
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

    def _start_pyaudio(self, pyaudio) -> None:
        self._p = pyaudio.PyAudio()
        mic, spk = self._resolve(pyaudio)
        self.mic_name = mic["name"]
        self.speaker_name = spk["name"].replace(" [Loopback]", "")
        self._mic = _Source(int(mic["defaultSampleRate"]), int(mic["maxInputChannels"]))
        self._spk = _Source(int(spk["defaultSampleRate"]), int(spk["maxInputChannels"]))
        self._streams = [self._open(pyaudio, mic, self._mic), self._open(pyaudio, spk, self._spk)]
        for s in self._streams:
            s.start_stream()

    def _start_soundcard(self, sc) -> None:
        devs, mics, spks = _sc_inputs(sc)
        dmic, dspk = _sc_defaults(sc, devs, mics, spks)
        pick = lambda i, default: i if i is not None and 0 <= i < len(devs) else default
        mic_i, spk_i = pick(self.mic_index, dmic), pick(self.speaker_index, dspk)
        if mic_i is None:
            raise AudioUnavailable("Couldn't find a microphone.")
        if spk_i is None:
            raise AudioUnavailable(_no_call_audio())
        mic, spk = devs[mic_i], devs[spk_i]
        self.mic_name, self.speaker_name = mic.name, spk.name
        self._mic, self._spk = _Source(TARGET_RATE, 1), _Source(TARGET_RATE, 1)  # the OS resamples to 16 kHz
        for device, source in ((mic, self._mic), (spk, self._spk)):
            try:
                self._readers.append(self._record(device, source))
            except AudioUnavailable as e:
                if device.isloopback or sys.platform != "win32" or e.__cause__ is None:  # not if it's just slow
                    raise
                try:  # SoundCard can't read some Windows mics (16-bit headsets such as EarPods); PortAudio can
                    self._streams.append(_sd_input(device.name, source))
                except Exception:
                    raise e from None

    def _record(self, device, source: _Source) -> threading.Thread:
        """One thread per device: SoundCard's record() blocks until a block is in."""
        ready, failed, stop = threading.Event(), [], self._stop  # this session's stop, even if it opens late

        def run() -> None:
            try:
                with device.recorder(samplerate=TARGET_RATE, blocksize=SC_BLOCK) as rec:
                    ready.set()
                    while not stop.is_set():
                        source.push_mono(rec.record(numframes=SC_BLOCK).mean(axis=1))
            except Exception as e:  # couldn't open, or the device went away mid-call (then it's silence)
                failed.append(e)
                ready.set()

        t = threading.Thread(target=run, name=f"audio-{device.name}", daemon=True)
        t.start()
        if not ready.wait(5):
            raise AudioUnavailable(f"{device.name} didn't respond. Try another device in Settings.")
        if failed:
            e = failed[0]
            raise AudioUnavailable(f"Couldn't open {device.name}: {str(e) or type(e).__name__}") from e
        return t

    # -- lifecycle -----------------------------------------------------
    def start(self) -> None:
        pyaudio, sc = _backend()
        self._stop = threading.Event()  # fresh per session, so a reader left over from the last one stays stopped
        try:
            if sc:
                self._start_soundcard(sc)
            else:
                self._start_pyaudio(pyaudio)
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
        for s in self._streams:  # PyAudio streams, or sounddevice ones on Windows on ARM
            try:
                (getattr(s, "stop_stream", None) or s.stop)()
                s.close()
            except Exception:
                pass
        self._streams = []
        for t in self._readers:
            t.join(timeout=1.0)
        self._readers = []
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
