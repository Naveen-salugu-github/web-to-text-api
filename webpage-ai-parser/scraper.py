from playwright.sync_api import sync_playwright


def fetch_page_html(url: str, timeout_ms: int = 30000) -> str:
    """Load a webpage with Playwright and return raw HTML."""
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            page.wait_for_load_state("networkidle", timeout=timeout_ms)
            html = page.content()
            return html
        finally:
            browser.close()
