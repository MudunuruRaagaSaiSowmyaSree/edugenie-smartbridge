from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.gemini_service import generate_content, GeminiQuotaError, GeminiServiceError

router = APIRouter()


class QuestionRequest(BaseModel):
    question: str


@router.post("/ask")
def ask_question(request: QuestionRequest):
    prompt = f"""
You are EduGenie, a helpful educational assistant.
Answer the student's question clearly and accurately.
Then add 2-3 sentences of extra educational context to help them learn more.

Question: {request.question}

Format your response as:
Answer: <direct answer>
Context: <additional educational context>
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

    return {"question": request.question, "response": result}