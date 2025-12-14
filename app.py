import socketio
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import os

# ---------- SOCKET ----------
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*"
)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# ---------- ASGI ----------
socket_app = socketio.ASGIApp(sio, app)

# ---------- CHAT ----------
@sio.event
async def connect(sid, environ):
    print("connect", sid)

@sio.event
async def disconnect(sid):
    print("disconnect", sid)

@sio.event
async def message(sid, data):
    await sio.emit("message", data)

@sio.event
async def typing(sid, user):
    await sio.emit("typing", user, skip_sid=sid)

# ---------- WEB ----------
@app.get("/", response_class=HTMLResponse)
async def index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()
