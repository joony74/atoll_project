from __future__ import annotations

import atexit
import os
import socket
import subprocess
import time
import urllib.request
from pathlib import Path

import webview


PROJECT_ROOT = Path(__file__).resolve().parent
STREAMLIT_ENTRY = PROJECT_ROOT / "app.py"
LOG_DIR = Path.home() / "Library" / "Application Support" / "CocoAIStudy"
LOG_PATH = LOG_DIR / "launcher.log"
COMMON_PATH_HINTS = (
    "/opt/homebrew/bin",
    "/opt/homebrew/sbin",
    "/usr/local/bin",
    "/usr/local/sbin",
    "/usr/bin",
    "/bin",
    "/usr/sbin",
    "/sbin",
)
SPLASH_HTML = """
<!doctype html>
<html lang="ko">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>CocoAi Study</title>
    <style>
      :root {
        color-scheme: dark;
        --bg-1: #2a2c37;
        --bg-2: #1f2129;
        --line: rgba(132, 143, 171, 0.18);
        --text-1: #edf2ff;
        --text-2: #aab4ca;
        --accent-1: #ff9b57;
        --accent-2: #7aa8ff;
      }
      * { box-sizing: border-box; }
      html, body {
        margin: 0;
        width: 100%;
        height: 100%;
        overflow: hidden;
        background: linear-gradient(180deg, var(--bg-1) 0%, var(--bg-2) 100%);
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Apple SD Gothic Neo", sans-serif;
      }
      body {
        display: grid;
        place-items: center;
      }
      .splash {
        width: min(540px, calc(100vw - 48px));
        padding: 32px 34px;
        border-radius: 26px;
        border: 1px solid var(--line);
        background: rgba(18, 20, 26, 0.46);
        box-shadow: 0 18px 54px rgba(0, 0, 0, 0.22);
        backdrop-filter: blur(12px);
      }
      .brand {
        margin: 0;
        font-size: 42px;
        line-height: 1;
        letter-spacing: -0.04em;
        font-weight: 800;
        color: var(--accent-1);
      }
      .brand span {
        color: var(--accent-2);
      }
      .title {
        margin: 16px 0 0;
        color: var(--text-1);
        font-size: 20px;
        font-weight: 700;
      }
      .subtitle {
        margin: 10px 0 0;
        color: var(--text-2);
        font-size: 14px;
        line-height: 1.6;
      }
      .loader {
        margin-top: 22px;
        display: flex;
        align-items: center;
        gap: 9px;
      }
      .loader span {
        width: 8px;
        height: 8px;
        border-radius: 999px;
        background: rgba(237, 242, 255, 0.88);
        animation: pulse 1.05s ease-in-out infinite;
      }
      .loader span:nth-child(2) { animation-delay: 0.15s; }
      .loader span:nth-child(3) { animation-delay: 0.3s; }
      @keyframes pulse {
        0%, 80%, 100% { opacity: 0.22; transform: translateY(0); }
        40% { opacity: 1; transform: translateY(-3px); }
      }
    </style>
  </head>
  <body>
    <section class="splash" aria-label="CocoAi Study loading">
      <h1 class="brand">COCO<span>AI</span></h1>
      <p class="title">코코앱을 준비하고 있어요</p>
      <p class="subtitle">학습리스트와 메인 대화를 빠르게 이어갈 수 있도록 실행 환경을 정리하는 중입니다.</p>
      <div class="loader" aria-hidden="true">
        <span></span><span></span><span></span>
      </div>
    </section>
  </body>
</html>
""".strip()


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
    merged_paths: list[str] = []
    for entry in (*COMMON_PATH_HINTS, *(env.get("PATH", "").split(os.pathsep))):
        cleaned = str(entry or "").strip()
        if cleaned and cleaned not in merged_paths:
            merged_paths.append(cleaned)
    env["PATH"] = os.pathsep.join(merged_paths)
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
    return subprocess.Popen(
        cmd,
        cwd=str(PROJECT_ROOT),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
    )


def _signal_streamlit_shutdown(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    try:
        process.terminate()
        _log("streamlit_terminate")
    except Exception as exc:
        _log(f"streamlit_terminate_failed {exc}")


def _stop_streamlit(process: subprocess.Popen[str], timeout: float = 0.45) -> None:
    _signal_streamlit_shutdown(process)
    deadline = time.time() + max(timeout, 0.0)
    while time.time() < deadline:
        if process.poll() is not None:
            _log("streamlit_exit_graceful")
            return
        time.sleep(0.05)

    if process.poll() is None:
        try:
            process.kill()
            _log("streamlit_kill")
        except Exception as exc:
            _log(f"streamlit_kill_failed {exc}")
    try:
        process.wait(timeout=0.4)
    except Exception:
        pass


def _stop_streamlit_if_any(process_holder: dict[str, subprocess.Popen[str] | None], timeout: float = 0.45) -> None:
    process = process_holder.get("process")
    if process is None:
        return
    _stop_streamlit(process, timeout=timeout)


def _prepare_quick_shutdown(window: webview.Window, process_holder: dict[str, subprocess.Popen[str] | None]) -> None:
    def _on_closing() -> None:
        _log("window_closing")
        process = process_holder.get("process")
        if process is not None:
            _signal_streamlit_shutdown(process)

    window.events.closing += _on_closing


def _render_startup_error(window: webview.Window, message: str) -> None:
    safe_message = str(message or "알 수 없는 오류").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    error_html = f"""
    <!doctype html>
    <html lang="ko">
      <head>
        <meta charset="utf-8" />
        <style>
          html, body {{
            margin: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(180deg, #2a2c37 0%, #1f2129 100%);
            color: #edf2ff;
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Apple SD Gothic Neo", sans-serif;
          }}
          body {{
            display: grid;
            place-items: center;
            padding: 24px;
            box-sizing: border-box;
          }}
          .card {{
            width: min(560px, 100%);
            padding: 28px 30px;
            border-radius: 24px;
            border: 1px solid rgba(249, 168, 179, 0.24);
            background: rgba(28, 21, 27, 0.72);
          }}
          h1 {{
            margin: 0 0 10px;
            font-size: 22px;
          }}
          p {{
            margin: 0;
            color: #f5c4cd;
            line-height: 1.6;
            font-size: 14px;
          }}
        </style>
      </head>
      <body>
        <section class="card">
          <h1>코코앱을 시작하지 못했어요</h1>
          <p>{safe_message}</p>
        </section>
      </body>
    </html>
    """.strip()
    try:
        window.load_html(error_html)
    except Exception as exc:
        _log(f"window_error_html_failed {exc}")


def _boot_streamlit_into_window(window: webview.Window, port: int, process_holder: dict[str, subprocess.Popen[str] | None]) -> None:
    url = f"http://127.0.0.1:{port}"
    try:
        process = _start_streamlit(port)
        process_holder["process"] = process
        _wait_for_server(url)
        _log(f"load_window_url {url}")
        window.load_url(url)
    except Exception as exc:
        _log(f"launcher_boot_failed {exc}")
        _render_startup_error(window, str(exc))


def main() -> int:
    _log("launcher_main_start")
    if not PYTHON_BIN.exists():
        _log(f"missing_python {PYTHON_BIN}")
        raise FileNotFoundError(f"Missing runtime python: {PYTHON_BIN}")
    if not STREAMLIT_ENTRY.exists():
        _log(f"missing_entry {STREAMLIT_ENTRY}")
        raise FileNotFoundError(f"Missing streamlit entry: {STREAMLIT_ENTRY}")

    port = _free_port()
    process_holder: dict[str, subprocess.Popen[str] | None] = {"process": None}
    atexit.register(lambda: _stop_streamlit_if_any(process_holder, timeout=0.1))
    _log("create_window")
    window = webview.create_window(
        "CocoAi Study",
        html=SPLASH_HTML,
        width=1400,
        height=920,
        text_select=True,
        background_color="#272934",
    )
    _prepare_quick_shutdown(window, process_holder)
    try:
        _log("webview_start")
        webview.start(_boot_streamlit_into_window, args=(window, port, process_holder))
    finally:
        _log("webview_exit")
        _stop_streamlit_if_any(process_holder)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
