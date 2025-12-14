import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request, redirect, session, send_from_directory
from flask_socketio import SocketIO, emit
import os, sqlite3, hashlib

app = Flask(__name__)
app.secret_key = "secret123"

socketio = SocketIO(app, async_mode="eventlet", cors_allowed_origins="*")

UPLOAD_FOLDER = "uploads"

# --- FIX FOR RENDER ---
if not os.path.isdir(UPLOAD_FOLDER):
    if os.path.exists(UPLOAD_FOLDER):
        os.remove(UPLOAD_FOLDER)
    os.mkdir(UPLOAD_FOLDER)

# ---------- DB ----------
def db():
    return sqlite3.connect("users.db")

with db() as c:
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT
        )
    """)

# ---------- AUTH ----------
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        u = request.form["username"]
        p = hashlib.sha256(request.form["password"].encode()).hexdigest()
        try:
            with db() as c:
                c.execute("INSERT INTO users VALUES (NULL,?,?)",(u,p))
            return redirect("/login")
        except:
            return "USER EXISTS"
    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = request.form["username"]
        p = hashlib.sha256(request.form["password"].encode()).hexdigest()
        r = db().execute(
            "SELECT * FROM users WHERE username=? AND password=?",(u,p)
        ).fetchone()
        if r:
            session["user"] = u
            return redirect("/")
    return render_template("login.html")

@app.route("/")
def index():
    if "user" not in session:
        return redirect("/login")
    return render_template("index.html", user=session["user"])

# ---------- FILE UPLOAD ----------
@app.route("/upload", methods=["POST"])
def upload():
    f = request.files["file"]
    path = os.path.join(UPLOAD_FOLDER, f.filename)
    f.save(path)
    return {"url": "/uploads/" + f.filename}

@app.route("/uploads/<name>")
def files(name):
    return send_from_directory(UPLOAD_FOLDER, name)

# ---------- SOCKET ----------
@socketio.on("message")
def msg(data):
    emit("message", data, broadcast=True)

@socketio.on("typing")
def typing(user):
    emit("typing", user, broadcast=True, include_self=False)

@socketio.on("stop_typing")
def stop():
    emit("stop_typing", broadcast=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port)
