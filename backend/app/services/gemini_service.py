import os
from pathlib import Path
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, GoogleAPIError
from dotenv import load_dotenv

# Explicitly point to backend/.env regardless of where uvicorn is run from
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
print("DEBUG - Loaded key:", GEMINI_API_KEY[:10] if GEMINI_API_KEY else "NOT FOUND")

genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel("gemini-3.8-flash")


class GeminiQuotaError(Exception):
    """Raised when the Gemini API free-tier quota has been exhausted (HTTP 429)."""
    def __init__(self, message: str, retry_after: float | None = None):
        self.retry_after = retry_after
        super().__init__(message)


class GeminiServiceError(Exception):
    """Raised for any other Gemini API failure."""
    pass


def generate_content(prompt: str) -> str:
    """
    Calls the Gemini model and returns the raw text response.
    Raises GeminiQuotaError / GeminiServiceError on failure instead of
    returning the error as a string, so callers can tell a real answer
    apart from a failure (and don't try to json.loads() an error message).
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except ResourceExhausted as e:
        retry_after = getattr(getattr(e, "retry_delay", None), "seconds", None)
        raise GeminiQuotaError(
            "Gemini API daily quota exceeded for this model/key.", retry_after
        ) from e
    except GoogleAPIError as e:
        raise GeminiServiceError(f"Gemini API error: {e}") from e
    except Exception as e:
        raise GeminiServiceError(f"Unexpected error calling Gemini: {e}") from e