"""
CLI chat client (uses Rich for display).

Flow:
  1. Ask for the server URL (the pinggy.io tunnel URL pointing at the Flask server)
  2. Ask for a username
  3. Join the chat, then loop: a background thread polls for new messages
     and prints them, while the main thread reads your input and sends it.

Commands:
  /exit   quit the chat
"""
import sys
import threading
import time
from datetime import datetime

import requests
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

console = Console()

POLL_INTERVAL = 1.0  # seconds


def normalize_url(url: str) -> str:
    url = url.strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
    return url.rstrip("/")


def fmt_time(ts: float) -> str:
    return datetime.fromtimestamp(ts).strftime("%H:%M:%S")


def print_message(msg: dict, me: str):
    ts = fmt_time(msg["ts"])
    user = msg["user"]
    text = msg["text"]

    if msg.get("type") in ("join", "leave"):
        console.print(f"[dim]{ts}[/dim] [italic yellow]* {text}[/italic yellow]")
        return

    if user == me:
        console.print(f"[dim]{ts}[/dim] [bold green]{user} (you)[/bold green]: {text}")
    else:
        console.print(f"[dim]{ts}[/dim] [bold cyan]{user}[/bold cyan]: {text}")


def poller(base_url: str, username: str, cursor_holder: dict, stop_event: threading.Event):
    while not stop_event.is_set():
        try:
            resp = requests.get(
                f"{base_url}/api/messages",
                params={"after": cursor_holder["cursor"]},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            for msg in data.get("messages", []):
                print_message(msg, username)
                cursor_holder["cursor"] = msg["id"]
        except requests.RequestException as exc:
            console.print(f"[red]Connection error: {exc}[/red]")
            time.sleep(2)
        time.sleep(POLL_INTERVAL)


def main():
    console.print(Panel.fit("[bold]Rich CLI Chat[/bold]", border_style="magenta"))

    raw_url = Prompt.ask("Server URL (from pinggy.io tunnel)")
    base_url = normalize_url(raw_url)

    try:
        health = requests.get(f"{base_url}/api/health", timeout=10)
        health.raise_for_status()
    except requests.RequestException as exc:
        console.print(f"[red]Could not reach server at {base_url}: {exc}[/red]")
        sys.exit(1)

    username = Prompt.ask("Your name").strip()
    while not username:
        username = Prompt.ask("Your name cannot be empty. Your name").strip()

    try:
        join_resp = requests.post(f"{base_url}/api/join", json={"username": username}, timeout=10)
        join_resp.raise_for_status()
        cursor_holder = {"cursor": join_resp.json().get("cursor", 0)}
    except requests.RequestException as exc:
        console.print(f"[red]Failed to join chat: {exc}[/red]")
        sys.exit(1)

    console.print(f"[green]Connected as {username}. Type /exit to quit.[/green]\n")

    stop_event = threading.Event()
    poll_thread = threading.Thread(
        target=poller, args=(base_url, username, cursor_holder, stop_event), daemon=True
    )
    poll_thread.start()

    try:
        while True:
            text = console.input("[bold]> [/bold]").strip()
            if not text:
                continue
            if text == "/exit":
                break
            try:
                requests.post(
                    f"{base_url}/api/messages",
                    json={"username": username, "text": text},
                    timeout=10,
                )
            except requests.RequestException as exc:
                console.print(f"[red]Failed to send message: {exc}[/red]")
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        stop_event.set()
        console.print("\n[yellow]Goodbye![/yellow]")


if __name__ == "__main__":
    main()
