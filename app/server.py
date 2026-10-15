"""Local web app: http://127.0.0.1:8765  (run with:  python -m app.server)"""
from __future__ import annotations

import argparse
import asyncio
import ctypes
import logging
import os
import secrets
import socket
import subprocess
import sys
import threading
import webbrowser
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, File, HTTPException, Request, UploadFile, WebSocket
from fastapi.responses import FileResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .config import DATA_DIR, STATIC_DIR
from .core import Core, SessionError

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s: %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("server")

core = Core()


@asynccontextmanager
async def lifespan(app: FastAPI):
    core.hub.loop = asyncio.get_running_loop()
    yield
    if core.session:
        await core.stop_session()


app = FastAPI(title="Interview Copilot", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# -- phone access ---------------------------------------------------------------------
# The app listens on your Wi-Fi so your phone can open it. Anything that isn't this computer
# needs the key inside the QR code (then a cookie), so others on the same network can't see
# your transcripts, answers or files.
COOKIE = "copilot_key"
_LOCAL = {"127.0.0.1", "::1"}
_port = int(os.environ.get("PORT", "8765"))


def _phone_key() -> str:
    path = DATA_DIR / "phone_key"
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError:
        key = secrets.token_urlsafe(18)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(key, encoding="utf-8")
        return key


PHONE_KEY = _phone_key()


def _allowed(host: Optional[str], key: Optional[str]) -> bool:
    return host in _LOCAL or secrets.compare_digest(key or "", PHONE_KEY)


def lan_ip() -> Optional[str]:
    """This computer's address on the local network (no packet is sent)."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        try:
            s.connect(("8.8.8.8", 80))  # picks the interface with the default route (your Wi-Fi)
            ip = s.getsockname()[0]
        except OSError:
            return None
    return None if ip.startswith("127.") else ip


def ensure_firewall(port: int) -> str:
    """Windows: a one-time firewall rule so devices on your own network (your phone) can connect.
    Adding it needs admin rights, so Windows asks once. Returns ok, added, declined or skipped."""
    if sys.platform != "win32":
        return "skipped"
    name = f"Interview Copilot (port {port})"
    try:
        if subprocess.run(["netsh", "advfirewall", "firewall", "show", "rule", f"name={name}"],
                          capture_output=True, timeout=15).returncode == 0:
            return "ok"
    except (OSError, subprocess.SubprocessError):
        return "skipped"
    # Only devices on your own subnet, on any network type, so the Wi-Fi can stay "Public".
    args = (f'advfirewall firewall add rule name="{name}" dir=in action=allow protocol=TCP '
            f"localport={port} remoteip=localsubnet")
    shown = ctypes.windll.shell32.ShellExecuteW(None, "runas", "netsh", args, None, 0)  # Windows permission prompt
    return "added" if shown > 32 else "declined"


@app.middleware("http")
async def phone_key_gate(request: Request, call_next):
    host = request.client.host if request.client else None
    if _allowed(host, request.cookies.get(COOKIE)):
        return await call_next(request)
    if _allowed(None, request.query_params.get("k")):  # first visit from the QR code
        resp = RedirectResponse(str(request.url.remove_query_params("k")), status_code=303)
        resp.set_cookie(COOKIE, PHONE_KEY, max_age=30 * 86400, httponly=True, samesite="lax")
        return resp
    return PlainTextResponse("Scan the QR code under Phone in Interview Copilot on your computer to open it here.",
                             status_code=403)


def _devices() -> dict:
    try:
        from .audio_capture import list_devices
        return {"available": True, **list_devices()}
    except Exception as e:
        return {"available": False, "error": str(e), "mics": [], "speakers": []}


def _info() -> dict:
    docs, trimmed = core.docs.combined()
    return {
        "settings": core.settings.public(),
        "docs": core.docs.list(),
        "docs_trimmed": trimmed,
    }


@app.get("/")
async def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/info")
async def info():
    return _info()


@app.get("/api/devices")
async def devices():
    return await asyncio.to_thread(_devices)


@app.get("/api/phone")
async def phone(request: Request):
    ip = lan_ip()
    if not ip:
        return {"url": None, "qr": None, "firewall": "skipped"}
    # Only when clicked on this computer: that's where Windows shows its permission prompt.
    local = request.client is not None and request.client.host in _LOCAL
    firewall = await asyncio.to_thread(ensure_firewall, _port) if local else "skipped"
    import segno
    url = f"http://{ip}:{_port}/?k={PHONE_KEY}"
    return {"url": url, "qr": segno.make(url, error="m").svg_data_uri(scale=8, dark="#000", light="#fff"),
            "firewall": firewall}


@app.post("/api/settings")
async def update_settings(changes: dict):
    # Audio/transcription changes apply the next time Record is pressed; AI changes apply immediately.
    try:
        core.settings.update(changes)
    except (TypeError, ValueError) as e:
        raise HTTPException(400, f"Invalid setting: {e}")
    return _info()


@app.post("/api/settings/clear-key/{name}")
async def clear_key(name: str):
    core.settings.clear_key(name)
    return _info()


class StartBody(BaseModel):
    demo: bool = False


@app.post("/api/start")
async def start(body: StartBody):
    try:
        await core.start_session(demo=body.demo)
    except SessionError as e:
        raise HTTPException(400, str(e))
    return {"ok": True}


@app.post("/api/stop")
async def stop():
    path = await core.stop_session()
    return {"ok": True, "saved": path}


class AnswerBody(BaseModel):
    question: str = ""


@app.post("/api/answer")
async def answer(body: AnswerBody):
    try:
        await core.manual_answer(body.question)
    except SessionError as e:
        raise HTTPException(400, str(e))
    return {"ok": True}


@app.post("/api/docs")
async def upload_docs(files: list[UploadFile] = File(...)):
    added, errors = [], []
    for f in files:
        data = await f.read()
        try:
            added.append(await asyncio.to_thread(core.docs.add_file, f.filename or "file", data))
        except ValueError as e:
            errors.append(str(e))
    return {**_info(), "added": added, "errors": errors}


class TextDoc(BaseModel):
    name: str = "Pasted notes"
    text: str


@app.post("/api/docs/text")
async def add_text_doc(body: TextDoc):
    try:
        core.docs.add_text(body.name, body.text)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return _info()


@app.delete("/api/docs/{doc_id}")
async def delete_doc(doc_id: str):
    core.docs.remove(doc_id)
    return _info()


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    if not _allowed(ws.client.host if ws.client else None, ws.cookies.get(COOKIE)):
        await ws.close(code=1008)
        return
    await ws.accept()
    await core.hub.serve(ws, {"info": _info()})


class HttpsProbeFilter(logging.Filter):
    """Phone browsers try https:// first, which this http-only server logs as "Invalid HTTP request
    received" on every attempt before the browser falls back to http. Explain it once instead."""

    def __init__(self):
        super().__init__()
        self.explained = False

    def filter(self, record: logging.LogRecord) -> bool:
        if record.getMessage() != "Invalid HTTP request received.":
            return True
        if self.explained:
            return False
        self.explained = True
        record.msg, record.args = ("A device (probably your phone's browser) tried a secure https:// link first. "
                                   "That's normal: it falls back to http and the page loads."), ()
        return True


def main() -> None:
    global _port
    import uvicorn

    parser = argparse.ArgumentParser(description="Interview Copilot")
    parser.add_argument("--port", type=int, default=_port)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()

    _port = args.port
    url = f"http://127.0.0.1:{args.port}"
    if not args.no_browser:
        threading.Timer(1.5, lambda: webbrowser.open(url)).start()
    phone = ("On your phone (same Wi-Fi): click Phone in the app and scan the QR code." if lan_ip()
             else "Phone access needs this computer to be on Wi-Fi or a network.")
    print(f"\n  Interview Copilot is running at {url}\n  {phone}\n  Keep this window open. Press Ctrl+C to quit.\n")
    # All interfaces so your phone can connect; phone_key_gate keeps other devices out.
    config = uvicorn.Config(app, host="0.0.0.0", port=args.port, log_level="warning")
    logging.getLogger("uvicorn.error").addFilter(HttpsProbeFilter())  # after Config set up logging
    uvicorn.Server(config).run()


if __name__ == "__main__":
    main()
