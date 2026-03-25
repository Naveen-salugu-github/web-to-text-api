import asyncio
import sys
from pathlib import Path

# Before Uvicorn creates a loop: Windows needs Proactor for subprocess (Playwright).
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, ConfigDict, HttpUrl

from ai_processor import structure_content_with_ai
from cleaner import clean_html
from scraper import fetch_page_html

load_dotenv(Path(__file__).parent / ".env")

app = FastAPI(title="Webpage -> AI-Ready Structured Data API")
# Swagger UI sometimes mis-renders OAS 3.1 response $refs; 3.0.2 displays reliably.
app.openapi_version = "3.0.2"


class ParsePageRequest(BaseModel):
    url: HttpUrl


class Section(BaseModel):
    """One block of structured content from the LLM."""

    model_config = ConfigDict(extra="ignore")
    heading: str = ""
    content: str = ""


class ParsePageResponse(BaseModel):
    """Shape of a successful `/parse-page` response (shown in OpenAPI /docs)."""

    title: str = ""
    summary: str = ""
    sections: list[Section] = []
    key_points: list[str] = []
    entities: list[str] = []


@app.get("/", response_class=HTMLResponse)
def docs_page() -> str:
    docs_path = Path(__file__).parent / "templates" / "docs.html"
    if not docs_path.exists():
        return "<h1>Docs page not found.</h1>"
    return docs_path.read_text(encoding="utf-8")


@app.post("/parse-page", response_model=ParsePageResponse)
async def parse_page(payload: ParsePageRequest) -> ParsePageResponse:
    try:
        html = await fetch_page_html(str(payload.url))
        cleaned = clean_html(html)

        if not cleaned.get("content"):
            raise HTTPException(status_code=422, detail="Could not extract readable content.")

        ai_result = structure_content_with_ai(cleaned["content"])
        return ParsePageResponse.model_validate(
            {
                "title": cleaned.get("title", ""),
                "summary": ai_result.get("summary", ""),
                "sections": ai_result.get("sections", []),
                "key_points": ai_result.get("key_points", []),
                "entities": ai_result.get("entities", []),
            }
        )
    except HTTPException:
        raise
    except Exception as exc:
        msg = str(exc) or repr(exc) or type(exc).__name__
        raise HTTPException(status_code=500, detail=msg) from exc
