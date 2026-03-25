from bs4 import BeautifulSoup


def _class_str(element) -> str:
    attrs = getattr(element, "attrs", None)
    if not attrs:
        return ""
    raw = attrs.get("class", [])
    if isinstance(raw, str):
        return raw.lower()
    return " ".join(raw).lower()


def _id_str(element) -> str:
    attrs = getattr(element, "attrs", None)
    if not attrs:
        return ""
    return (attrs.get("id") or "").lower()


def clean_html(html: str) -> dict:
    """Extract title and cleaned readable content from HTML."""
    soup = BeautifulSoup(html, "html.parser")

    # Remove noisy elements that usually do not help extraction.
    for tag_name in ["script", "style", "nav", "header", "footer", "aside", "noscript"]:
        for element in soup.find_all(tag_name):
            element.decompose()

    # Remove common ad/promo containers by class or id hint.
    # Avoid matching "ad" alone — it matches class names like "padding", "lead", etc.
    ad_hints = [
        "advert",
        "advertisement",
        "adsbygoogle",
        "sponsor",
        "promo",
        "cookie",
        "banner",
        "google-ad",
    ]
    for element in soup.find_all(True):
        cls = _class_str(element)
        elem_id = _id_str(element)
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

    # Many sites put prose in divs/spans, not <p>/<h*>. Fall back to main/article/body text.
    if not content:
        root = soup.find("main") or soup.find("article") or soup.body
        if root:
            content = root.get_text("\n", strip=True)

    return {"title": page_title, "content": content}
