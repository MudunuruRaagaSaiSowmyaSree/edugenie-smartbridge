from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import qa, quiz, summarize, learning_path, flashcards

app = FastAPI(title="EduGenie API", version="1.0.0")
app.include_router(qa.router, prefix="/api", tags=["Q&A"])
app.include_router(quiz.router, prefix="/api/quiz", tags=["Quiz"])
app.include_router(summarize.router, prefix="/api/summarize", tags=["Summarize"])
app.include_router(learning_path.router, prefix="/api/learning-path", tags=["Learning Path"])
app.include_router(flashcards.router, prefix="/api/flashcards", tags=["Flashcards"])

# Allow frontend (HTML/CSS/JS) to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for development; we'll restrict this later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "EduGenie API is running 🚀"}

@app.get("/health")
def health_check():
    return {"status": "ok"}