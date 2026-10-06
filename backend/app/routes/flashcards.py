import json
import re
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.gemini_service import generate_content, GeminiQuotaError, GeminiServiceError

router = APIRouter()


class FlashcardRequest(BaseModel):
    topic: str
    num_cards: int = 5


def clean_json_response(raw_text: str) -> dict:
    cleaned = re.sub(r"^```json\s*|```$", "", raw_text.strip(), flags=re.MULTILINE).strip()
    return json.loads(cleaned)


@router.post("/generate")
def generate_flashcards(request: FlashcardRequest):
    prompt = f"""
You are EduGenie, an educational flashcard generator.
Create {request.num_cards} flashcards on the topic: "{request.topic}".
Each flashcard should have a short "front" (a term, question, or concept) and a clear, concise "back" (the definition or answer).

Return ONLY valid JSON in this exact format, with no extra text before or after:
{{
  "topic": "{request.topic}",
  "flashcards": [
    {{
      "front": "...",
      "back": "..."
    }}
  ]
}}
"""
    try:
        raw_result = generate_content(prompt)
    except GeminiQuotaError as e:
        raise HTTPException(
            status_code=429,
            detail=f"Daily AI quota reached, try again later. ({e})"
        )
    except GeminiServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))

    try:
        return clean_json_response(raw_result)
    except json.JSONDecodeError:
        return {
            "topic": request.topic,
            "error": "Failed to parse flashcards JSON",
            "raw_response": raw_result
        }