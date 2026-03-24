from bs4 import BeautifulSoup


def clean_html(html: str) -> dict:
    """Extract title and cleaned readable content from HTML."""
    soup = BeautifulSoup(html, "html.parser")

    # Remove noisy elements that usually do not help extraction.
    for tag_name in ["script", "style", "nav", "header", "footer", "aside", "noscript"]:
        for element in soup.find_all(tag_name):
            element.decompose()

    # Remove common ad/promo containers by class or id hint.
    ad_hints = ["ad", "ads", "advert", "sponsor", "promo", "cookie", "banner"]
    for element in soup.find_all(True):
        cls = " ".join(element.get("class", [])).lower()
        elem_id = (element.get("id") or "").lower()
        if any(hint in cls or hint in elem_id for hint in ad_hints):
            element.decompose()

    page_title = ""
    if soup.title and soup.title.string:
        page_title = soup.title.string.strip()

    text_blocks = []
    for tag in soup.find_all(["h1", "h2", "h3", "p"]):
        text = tag.get_text(" ", strip=True)
        if not text:
            continue

        if tag.name in {"h1", "h2", "h3"}:
            text_blocks.append(f"\n## {text}\n")
        else:
            text_blocks.append(text)

    content = "\n".join(text_blocks).strip()
    return {"title": page_title, "content": content}
