"""Local web app: http://127.0.0.1:8765  (run with:  python -m app.server)"""
from __future__ import annotations

import argparse
import asyncio
import logging
import os
import threading
import webbrowser
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, HTTPException, UploadFile, WebSocket
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .config import STATIC_DIR
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
    await ws.accept()
    await core.hub.serve(ws, {"info": _info()})


def main() -> None:
    import uvicorn

    parser = argparse.ArgumentParser(description="Interview Copilot")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8765")))
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()

    url = f"http://127.0.0.1:{args.port}"
    if not args.no_browser:
        threading.Timer(1.5, lambda: webbrowser.open(url)).start()
    print(f"\n  Interview Copilot is running at {url}\n  Keep this window open. Press Ctrl+C to quit.\n")
    uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
