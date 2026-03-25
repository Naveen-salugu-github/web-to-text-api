import asyncio
import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import requests

_WORKER = Path(__file__).resolve().parent / "_playwright_worker.py"
logger = logging.getLogger(__name__)


def _fetch_via_requests(url: str, timeout_ms: int = 30000) -> str:
    """Plain HTTP fetch (no JS). Used when Playwright cannot run on this machine."""
    timeout = max(5.0, min(timeout_ms / 1000.0, 120.0))
    r = requests.get(
        url,
        timeout=timeout,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; WebpageAIParser/1.0)",
            "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
        },
    )
    r.raise_for_status()
    return r.text


def _run_playwright_subprocess(url: str, timeout_ms: int) -> str:
    """Spawn a clean Python process that runs Playwright (no Uvicorn / asyncio)."""
    if not _WORKER.is_file():
        raise FileNotFoundError(f"Missing worker script: {_WORKER}")

    timeout_sec = max(60.0, timeout_ms / 1000.0 + 45.0)

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".html", encoding="utf-8") as tmp:
        out_path = tmp.name

    try:
        cmd = [sys.executable, str(_WORKER), url, str(timeout_ms), out_path]
        kwargs: dict = {
            "capture_output": True,
            "text": True,
            "encoding": "utf-8",
            "errors": "replace",
            "timeout": timeout_sec,
        }
        if sys.platform == "win32" and hasattr(subprocess, "CREATE_NO_WINDOW"):
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

        proc = subprocess.run(cmd, **kwargs)
        if proc.returncode != 0:
            err = (proc.stderr or proc.stdout or "").strip() or f"exit {proc.returncode}"
            raise RuntimeError(f"Playwright worker failed: {err}")

        return Path(out_path).read_text(encoding="utf-8", errors="replace")
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"Playwright worker timed out: {exc}") from exc
    finally:
        try:
            os.unlink(out_path)
        except OSError:
            pass


async def fetch_page_html(url: str, timeout_ms: int = 30000) -> str:
    """Load a webpage: try Playwright (separate process), then plain HTTP if that fails."""
    if os.environ.get("FETCH_ONLY", "").lower() in ("requests", "http", "1", "true", "yes"):
        return await asyncio.to_thread(_fetch_via_requests, url, timeout_ms)
    try:
        return await asyncio.to_thread(_run_playwright_subprocess, url, timeout_ms)
    except Exception as exc:
        logger.warning("Playwright fetch failed; using HTTP requests fallback. %s", exc)
        return await asyncio.to_thread(_fetch_via_requests, url, timeout_ms)
