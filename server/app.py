"""
Flask chat server (REST polling based).

Endpoints:
  POST /api/join
      body: {"username": "..."}
      -> registers a join event, returns current message id cursor

  POST /api/messages
      body: {"username": "...", "text": "..."}
      -> appends a message, broadcasts it to all pollers

  GET /api/messages?after=<id>
      -> returns all messages with id > after, plus the latest id

  GET /api/health
      -> simple healthcheck
"""
import itertools
import threading
import time

from flask import Flask, jsonify, request

app = Flask(__name__)

_lock = threading.Lock()
_messages = []  # list of dicts: {id, user, text, ts, type}
_id_counter = itertools.count(1)


def _add_message(user, text, msg_type="chat"):
    with _lock:
        msg = {
            "id": next(_id_counter),
            "user": user,
            "text": text,
            "ts": time.time(),
            "type": msg_type,  # "chat", "join", "leave"
        }
        _messages.append(msg)
        # keep memory bounded
        if len(_messages) > 2000:
            del _messages[: len(_messages) - 2000]
        return msg


@app.get("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/api/join")
def join():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    if not username:
        return jsonify({"error": "username is required"}), 400

    msg = _add_message(username, f"{username} joined the chat", msg_type="join")
    with _lock:
        latest_id = _messages[-1]["id"] if _messages else 0
    return jsonify({"ok": True, "cursor": latest_id, "message": msg})


@app.post("/api/messages")
def post_message():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    text = (data.get("text") or "").strip()
    if not username or not text:
        return jsonify({"error": "username and text are required"}), 400

    msg = _add_message(username, text, msg_type="chat")
    return jsonify({"ok": True, "message": msg})


@app.get("/api/messages")
def get_messages():
    try:
        after = int(request.args.get("after", 0))
    except ValueError:
        after = 0

    with _lock:
        new_messages = [m for m in _messages if m["id"] > after]
        latest_id = _messages[-1]["id"] if _messages else after

    return jsonify({"messages": new_messages, "cursor": latest_id})


if __name__ == "__main__":
    # 0.0.0.0 so the pinggy.io SSH tunnel can reach it
    app.run(host="0.0.0.0", port=5000, threaded=True)
