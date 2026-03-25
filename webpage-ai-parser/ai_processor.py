import json
import os
from typing import Any, Dict

from groq import APIStatusError, BadRequestError, Groq, GroqError

# Groq retires model IDs over time; override via GROQ_MODEL. See https://console.groq.com/docs/models
DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"
# Rough cap so huge pages stay within context; tune via env if needed.
MAX_INPUT_CHARS = int(os.getenv("GROQ_MAX_INPUT_CHARS", "48000"))


def _extract_json_object(text: str) -> Dict[str, Any]:
    """Best-effort extraction of a JSON object from model output."""
    text = text.strip()

    # Try direct parse first.
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Fallback for fenced or surrounding text.
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = text[start : end + 1]
        return json.loads(candidate)

    raise ValueError("Model response did not contain valid JSON.")


def structure_content_with_ai(content: str) -> dict:
    """Use Groq LLM to convert cleaned text into structured JSON."""
    api_key = (os.getenv("GROQ_API_KEY") or "").strip()
    if not api_key:
        raise ValueError(
            "Missing GROQ_API_KEY. Set it in Railway: open your web service → Variables → "
            "add GROQ_API_KEY (same value as local .env), save, then redeploy."
        )

    if len(content) > MAX_INPUT_CHARS:
        content = content[:MAX_INPUT_CHARS] + "\n\n[...truncated for model context limit...]"

    client = Groq(api_key=api_key)
    model = os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL)

    prompt = (
        "You are an AI that converts webpage text into structured knowledge useful for AI agents.\n\n"
        "Return ONLY valid JSON with this exact structure:\n"
        "{\n"
        '  "summary": "string",\n'
        '  "sections": [\n'
        '    {"heading": "string", "content": "string"}\n'
        "  ],\n"
        '  "key_points": ["string"],\n'
        '  "entities": ["string"]\n'
        "}\n\n"
        f"Text:\n{content}"
    )

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Return concise, factual JSON only."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
    except BadRequestError as exc:
        raise ValueError(
            f"Groq rejected the request (check GROQ_MODEL; default is {DEFAULT_GROQ_MODEL}). {exc}"
        ) from exc
    except APIStatusError as exc:
        raise ValueError(f"Groq API error: {exc}") from exc
    except GroqError as exc:
        raise ValueError(f"Groq client error: {exc}") from exc

    raw_output = response.choices[0].message.content or "{}"
    structured = _extract_json_object(raw_output)

    # Normalize minimal shape for robustness.
    return {
        "summary": structured.get("summary", ""),
        "sections": structured.get("sections", []),
        "key_points": structured.get("key_points", []),
        "entities": structured.get("entities", []),
    }
