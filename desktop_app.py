from __future__ import annotations

import atexit
import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import webview


PROJECT_ROOT = Path(__file__).resolve().parent
STREAMLIT_ENTRY = PROJECT_ROOT / "app.py"
LOG_DIR = Path.home() / "Library" / "Application Support" / "CocoAIStudy"
LOG_PATH = LOG_DIR / "launcher.log"


def _resolve_python_bin() -> Path:
    candidates = [
        PROJECT_ROOT / "venv_clean" / "bin" / "python",
        PROJECT_ROOT / "venv" / "bin" / "python",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


PYTHON_BIN = _resolve_python_bin()


def _log(message: str) -> None:
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with LOG_PATH.open("a", encoding="utf-8") as fh:
            fh.write(f"[{timestamp}] {message}\n")
    except Exception:
        pass


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for_server(url: str, timeout: float = 30.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1.5):
                _log(f"server_ready {url}")
                return
        except Exception:
            time.sleep(0.25)
    raise TimeoutError(f"Streamlit server did not start: {url}")


def _start_streamlit(port: int) -> subprocess.Popen[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT)
    cmd = [
        str(PYTHON_BIN),
        "-m",
        "streamlit",
        "run",
        str(STREAMLIT_ENTRY),
        "--server.headless",
        "true",
        "--server.address",
        "127.0.0.1",
        "--server.port",
        str(port),
        "--browser.gatherUsageStats",
        "false",
    ]
    _log(f"start_streamlit python={PYTHON_BIN} port={port}")
    return subprocess.Popen(cmd, cwd=str(PROJECT_ROOT), env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True)


def _raise_window(window: webview.Window) -> None:
    try:
        if not window.events.shown.wait(15):
            _log("window_not_shown")
            return
        time.sleep(0.35)
        try:
            window.restore()
            window.show()
            _log("window_restore_show")
        except Exception as exc:
            _log(f"window_restore_show_failed {exc}")
        try:
            subprocess.run(
                ["osascript", "-e", 'tell application "CocoAi Study" to activate'],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                text=True,
            )
            _log("window_activate")
        except Exception as exc:
            _log(f"window_activate_failed {exc}")
    except Exception as exc:
        _log(f"window_raise_failed {exc}")


def main() -> int:
    _log("launcher_main_start")
    if not PYTHON_BIN.exists():
        _log(f"missing_python {PYTHON_BIN}")
        raise FileNotFoundError(f"Missing runtime python: {PYTHON_BIN}")
    if not STREAMLIT_ENTRY.exists():
        _log(f"missing_entry {STREAMLIT_ENTRY}")
        raise FileNotFoundError(f"Missing streamlit entry: {STREAMLIT_ENTRY}")

    port = _free_port()
    url = f"http://127.0.0.1:{port}"
    process = _start_streamlit(port)
    atexit.register(lambda: process.poll() is None and process.terminate())
    _wait_for_server(url)
    _log("create_window")
    window = webview.create_window("CocoAi Study", url, width=1400, height=920, text_select=True)
    try:
        _log("webview_start")
        webview.start(_raise_window, args=(window,))
    finally:
        _log("webview_exit")
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except Exception:
                process.kill()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
