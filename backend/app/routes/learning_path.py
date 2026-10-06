from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.gemini_service import generate_content, GeminiQuotaError, GeminiServiceError

router = APIRouter()


class LearningPathRequest(BaseModel):
    topic: str
    current_level: str = "beginner"  # beginner, intermediate, advanced


@router.post("/generate")
def generate_learning_path(request: LearningPathRequest):
    prompt = f"""
You are EduGenie, an educational assistant that creates personalized learning roadmaps.
Create a structured learning path for the topic: "{request.topic}".
The learner's current level is: {request.current_level}.

Organize the path into three stages: Beginner, Intermediate, and Advanced.
For each stage, list 3-5 specific subtopics or skills to learn, in logical progression order.
Also include a brief study recommendation (e.g. suggested resources type, practice approach) for each stage.

Return ONLY valid JSON in this exact format, with no extra text before or after:
{{
  "topic": "{request.topic}",
  "current_level": "{request.current_level}",
  "path": [
    {{
      "stage": "Beginner",
      "subtopics": ["...", "..."],
      "recommendation": "..."
    }},
    {{
      "stage": "Intermediate",
      "subtopics": ["...", "..."],
      "recommendation": "..."
    }},
    {{
      "stage": "Advanced",
      "subtopics": ["...", "..."],
      "recommendation": "..."
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

    import json
    import re

    try:
        cleaned = re.sub(r"^```json\s*|```$", "", raw_result.strip(), flags=re.MULTILINE).strip()
        parsed_result = json.loads(cleaned)
        return parsed_result
    except json.JSONDecodeError:
        return {
            "topic": request.topic,
            "error": "Failed to parse learning path JSON",
            "raw_response": raw_result
        }