import json
import os
from typing import Any, Dict

from groq import Groq


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
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("Missing GROQ_API_KEY environment variable.")

    client = Groq(api_key=api_key)

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

    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[
            {"role": "system", "content": "Return concise, factual JSON only."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )

    raw_output = response.choices[0].message.content or "{}"
    structured = _extract_json_object(raw_output)

    # Normalize minimal shape for robustness.
    return {
        "summary": structured.get("summary", ""),
        "sections": structured.get("sections", []),
        "key_points": structured.get("key_points", []),
        "entities": structured.get("entities", []),
    }
