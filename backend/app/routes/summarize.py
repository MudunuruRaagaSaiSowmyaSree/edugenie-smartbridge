from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.gemini_service import generate_content, GeminiQuotaError, GeminiServiceError

router = APIRouter()


class SummarizeRequest(BaseModel):
    text: str
    length: str = "medium"  # short, medium, detailed


@router.post("/text")
def summarize_text(request: SummarizeRequest):
    length_instruction = {
        "short": "in 2-3 sentences",
        "medium": "in one concise paragraph (5-6 sentences)",
        "detailed": "in a detailed summary with key points as bullet points"
    }.get(request.length, "in one concise paragraph")

    prompt = f"""
You are EduGenie, an educational assistant that helps students study efficiently.
Summarize the following educational text {length_instruction}.
Focus on the key concepts a student needs to remember for exams.

Text to summarize:
\"\"\"
{request.text}
\"\"\"

Return only the summary, no extra commentary.
"""
    try:
        result = generate_content(prompt)
    except GeminiQuotaError as e:
        raise HTTPException(
            status_code=429,
            detail=f"Daily AI quota reached, try again later. ({e})"
        )
    except GeminiServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))

    return {"original_length": len(request.text), "summary": result}