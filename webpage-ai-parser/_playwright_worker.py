"""
Run Playwright in a standalone process (invoked by scraper.py).

Uvicorn on Windows uses an asyncio loop that cannot spawn the browser
subprocess. A fresh Python interpreter has no such restriction.
"""
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright


def main() -> None:
    if len(sys.argv) < 4:
        print("usage: _playwright_worker.py <url> <timeout_ms> <output_html_path>", file=sys.stderr)
        sys.exit(2)
    url = sys.argv[1]
    timeout_ms = int(sys.argv[2])
    out_path = Path(sys.argv[3])

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(url, wait_until="load", timeout=timeout_ms)
            time.sleep(1.5)
            html = page.content()
        finally:
            browser.close()

    out_path.write_text(html, encoding="utf-8", errors="replace")


if __name__ == "__main__":
    main()
