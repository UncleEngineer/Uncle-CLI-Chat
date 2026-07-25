"""
GUI chat client (Tkinter version of chat_client.py).

Flow:
  1. Enter the server URL (the pinggy.io tunnel URL pointing at the Flask server)
  2. Enter a username, click Connect
  3. Chat window opens: a background thread polls for new messages and
     displays them, while the entry box + Send button post your messages.

Only dependency beyond the standard library is `requests`
(tkinter ships with Python).
"""
import queue
import threading
import time
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, scrolledtext

import requests

POLL_INTERVAL = 1.0  # seconds


def normalize_url(url: str) -> str:
    url = url.strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
    return url.rstrip("/")


def fmt_time(ts: float) -> str:
    return datetime.fromtimestamp(ts).strftime("%H:%M:%S")


class ChatApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Chat")
        self.root.geometry("520x480")

        self.base_url = None
        self.username = None
        self.cursor = 0
        self.stop_event = threading.Event()
        self.ui_queue: "queue.Queue[tuple]" = queue.Queue()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self._build_connect_frame()
        self.root.after(100, self._process_queue)

    # ---------- Connect screen ----------

    def _build_connect_frame(self):
        self.connect_frame = tk.Frame(self.root, padx=20, pady=20)
        self.connect_frame.pack(expand=True)

        tk.Label(self.connect_frame, text="Server URL (from pinggy.io tunnel)").grid(
            row=0, column=0, sticky="w", pady=(0, 4)
        )
        self.url_entry = tk.Entry(self.connect_frame, width=45)
        self.url_entry.grid(row=1, column=0, pady=(0, 12))
        self.url_entry.focus_set()

        tk.Label(self.connect_frame, text="Your name").grid(row=2, column=0, sticky="w", pady=(0, 4))
        self.name_entry = tk.Entry(self.connect_frame, width=45)
        self.name_entry.grid(row=3, column=0, pady=(0, 12))

        self.connect_button = tk.Button(self.connect_frame, text="Connect", command=self.on_connect)
        self.connect_button.grid(row=4, column=0, pady=(4, 0))

        self.status_label = tk.Label(self.connect_frame, text="", fg="red")
        self.status_label.grid(row=5, column=0, pady=(8, 0))

        self.root.bind("<Return>", lambda e: self.on_connect())

    def on_connect(self):
        url = self.url_entry.get().strip()
        name = self.name_entry.get().strip()

        if not url or not name:
            self.status_label.config(text="Please fill in both fields.")
            return

        self.base_url = normalize_url(url)
        self.username = name
        self.connect_button.config(state="disabled")
        self.status_label.config(text="Connecting...", fg="black")

        threading.Thread(target=self._connect_worker, daemon=True).start()

    def _connect_worker(self):
        try:
            resp = requests.get(f"{self.base_url}/api/health", timeout=10)
            resp.raise_for_status()

            join_resp = requests.post(
                f"{self.base_url}/api/join", json={"username": self.username}, timeout=10
            )
            join_resp.raise_for_status()
            cursor = join_resp.json().get("cursor", 0)
            self.ui_queue.put(("connected", cursor))
        except requests.RequestException as exc:
            self.ui_queue.put(("connect_error", str(exc)))

    # ---------- Chat screen ----------

    def _build_chat_frame(self):
        self.connect_frame.destroy()
        self.root.unbind("<Return>")
        self.root.title(f"Chat - {self.username}")

        chat_frame = tk.Frame(self.root)
        chat_frame.pack(fill="both", expand=True, padx=8, pady=8)

        self.log = scrolledtext.ScrolledText(chat_frame, state="disabled", wrap="word")
        self.log.pack(fill="both", expand=True, pady=(0, 8))
        self.log.tag_config("me", foreground="#1a7a1a", font=("TkDefaultFont", 10, "bold"))
        self.log.tag_config("other", foreground="#0a5ba8", font=("TkDefaultFont", 10, "bold"))
        self.log.tag_config("system", foreground="#a68a00", font=("TkDefaultFont", 9, "italic"))
        self.log.tag_config("time", foreground="#888888", font=("TkDefaultFont", 8))

        input_frame = tk.Frame(chat_frame)
        input_frame.pack(fill="x")

        self.msg_entry = tk.Entry(input_frame)
        self.msg_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.msg_entry.bind("<Return>", lambda e: self.send_message())
        self.msg_entry.focus_set()

        self.send_button = tk.Button(input_frame, text="Send", command=self.send_message)
        self.send_button.pack(side="right")

        self.stop_event.clear()
        threading.Thread(target=self._poller_worker, daemon=True).start()

    def send_message(self):
        text = self.msg_entry.get().strip()
        if not text:
            return
        self.msg_entry.delete(0, tk.END)
        threading.Thread(target=self._send_worker, args=(text,), daemon=True).start()

    def _send_worker(self, text: str):
        try:
            requests.post(
                f"{self.base_url}/api/messages",
                json={"username": self.username, "text": text},
                timeout=10,
            )
        except requests.RequestException as exc:
            self.ui_queue.put(("send_error", str(exc)))

    def _poller_worker(self):
        while not self.stop_event.is_set():
            try:
                resp = requests.get(
                    f"{self.base_url}/api/messages", params={"after": self.cursor}, timeout=10
                )
                resp.raise_for_status()
                data = resp.json()
                for msg in data.get("messages", []):
                    self.ui_queue.put(("message", msg))
                    self.cursor = msg["id"]
            except requests.RequestException as exc:
                self.ui_queue.put(("poll_error", str(exc)))
                time.sleep(2)
            time.sleep(POLL_INTERVAL)

    # ---------- Queue processing (runs on the Tk main thread) ----------

    def _process_queue(self):
        try:
            while True:
                kind, payload = self.ui_queue.get_nowait()

                if kind == "connected":
                    self.cursor = payload
                    self._build_chat_frame()

                elif kind == "connect_error":
                    self.connect_button.config(state="normal")
                    self.status_label.config(text=f"Could not connect: {payload}", fg="red")

                elif kind == "message":
                    self._append_message(payload)

                elif kind in ("send_error", "poll_error"):
                    self._append_system_line(f"[connection error] {payload}")

        except queue.Empty:
            pass
        finally:
            self.root.after(100, self._process_queue)

    def _append_message(self, msg: dict):
        self.log.config(state="normal")
        ts = fmt_time(msg["ts"])
        user = msg["user"]
        text = msg["text"]

        self.log.insert("end", f"{ts}  ", "time")
        if msg.get("type") in ("join", "leave"):
            self.log.insert("end", f"* {text}\n", "system")
        elif user == self.username:
            self.log.insert("end", f"{user} (you): ", "me")
            self.log.insert("end", f"{text}\n")
        else:
            self.log.insert("end", f"{user}: ", "other")
            self.log.insert("end", f"{text}\n")

        self.log.config(state="disabled")
        self.log.see("end")

    def _append_system_line(self, text: str):
        self.log.config(state="normal")
        self.log.insert("end", f"{text}\n", "system")
        self.log.config(state="disabled")
        self.log.see("end")

    def on_close(self):
        self.stop_event.set()
        self.root.destroy()


def main():
    root = tk.Tk()
    ChatApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
