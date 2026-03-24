from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, HttpUrl

from ai_processor import structure_content_with_ai
from cleaner import clean_html
from scraper import fetch_page_html

load_dotenv()

app = FastAPI(title="Webpage -> AI-Ready Structured Data API")


class ParsePageRequest(BaseModel):
    url: HttpUrl


@app.get("/", response_class=HTMLResponse)
def docs_page() -> str:
    docs_path = Path(__file__).parent / "templates" / "docs.html"
    if not docs_path.exists():
        return "<h1>Docs page not found.</h1>"
    return docs_path.read_text(encoding="utf-8")


@app.post("/parse-page")
def parse_page(payload: ParsePageRequest) -> dict:
    try:
        html = fetch_page_html(str(payload.url))
        cleaned = clean_html(html)

        if not cleaned.get("content"):
            raise HTTPException(status_code=422, detail="Could not extract readable content.")

        ai_result = structure_content_with_ai(cleaned["content"])
        return {
            "title": cleaned.get("title", ""),
            "summary": ai_result.get("summary", ""),
            "sections": ai_result.get("sections", []),
            "key_points": ai_result.get("key_points", []),
            "entities": ai_result.get("entities", []),
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
