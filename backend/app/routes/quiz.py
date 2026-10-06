import json
import re
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.gemini_service import generate_content, GeminiQuotaError, GeminiServiceError

router = APIRouter()


class QuizRequest(BaseModel):
    topic: str
    num_questions: int = 5
    difficulty: str = "medium"  # easy, medium, hard


def clean_json_response(raw_text: str) -> dict:
    """
    Removes markdown code fences (```json ... ```) if present,
    then parses the text into real JSON.
    """
    cleaned = re.sub(r"^```json\s*|```$", "", raw_text.strip(), flags=re.MULTILINE).strip()
    return json.loads(cleaned)


@router.post("/generate")
def generate_quiz(request: QuizRequest):
    prompt = f"""
You are EduGenie, an educational quiz generator.
Create {request.num_questions} multiple-choice questions on the topic: "{request.topic}".
Difficulty level: {request.difficulty}.

For each question, provide:
1. The question text
2. Four options labeled A, B, C, D
3. The correct answer letter
4. A short explanation of why it's correct

Return ONLY valid JSON in this exact format, with no extra text before or after:
{{
  "topic": "{request.topic}",
  "questions": [
    {{
      "question": "...",
      "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
      "correct_answer": "A",
      "explanation": "..."
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
        parsed_result = clean_json_response(raw_result)
        return parsed_result
    except json.JSONDecodeError:
        return {
            "topic": request.topic,
            "error": "Failed to parse quiz JSON",
            "raw_response": raw_result
        }