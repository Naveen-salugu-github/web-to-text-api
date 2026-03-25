"""
Start the API.

Usage (from repo root):
  python run.py

Important: open the docs in your browser with **http://** — not https://
(local uvicorn has no TLS; https will show a connection error).

Reload is off by default (more stable on Windows). To enable:
  set RELOAD=1
  python run.py

If port 8000 is busy (WinError 10048), either stop the old server or use another port:
  set PORT=8001
  python run.py
"""
import os
import pathlib

import uvicorn

_ROOT = pathlib.Path(__file__).resolve().parent
_LOG = _ROOT / "uvicorn_minimal.json"


if __name__ == "__main__":
    reload = os.environ.get("RELOAD", "").lower() in ("1", "true", "yes")
    log_config = str(_LOG) if _LOG.is_file() else None
    try:
        port = int(os.environ.get("PORT", "8000"))
    except ValueError:
        port = 8000

    print()
    print(f"  >>> Open the API docs at:  http://127.0.0.1:{port}/docs")
    print("  >>> (Use http://  NOT  https://  — localhost has no SSL certificate)")
    print("  >>> Reload:", "ON" if reload else "OFF (set RELOAD=1 to enable)")
    print(f"  >>> Port: {port}  (set PORT=8001 if 8000 is already in use)")
    print()

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=port,
        reload=reload,
        log_config=log_config,
    )
