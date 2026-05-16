from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
# Force redeploy v2
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.models.schemas import AskRequest, AskResponse, MCQRequest, MCQResponse
from app.services.ai_service import ai_service
from app.services.question_bank import load_bank, add_mcq, search_bank
from pydantic import BaseModel
from typing import Dict, List
import os

app = FastAPI(title=settings.APP_NAME, version=settings.VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static", html=True), name="static")


# MCQ Item model for question bank
class MCQItem(BaseModel):
    question: str
    options: Dict[str, str]
    correct: str
    explanation: str
    topic: str = ""
    difficulty: str = "medium"

@app.get("/")
async def root():
    return {"app": settings.APP_NAME, "version": settings.VERSION}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest):
    # If bank is to be used, retrieve relevant context
    bank_context = ""
    if request.use_bank:
        results = search_bank(request.question, top_k=3)
        if results:
            bank_context = "Here are some relevant questions from your personal bank:\n"
            for i, mcq in enumerate(results, 1):
                bank_context += f"{i}. Q: {mcq['question']}\n   Explanation: {mcq['explanation']}\n\n"
            bank_context += "Use this context to inform your answer.\n\n"

    result = await ai_service.ask(
        question=request.question,
        language=request.language,
        mode=request.mode,
        extra_context=bank_context
    )
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["answer"])
    return AskResponse(**result)


@app.post("/mcq", response_model=MCQResponse)
async def generate_mcq(request: MCQRequest):
    result = await ai_service.generate_mcq(request.topic, request.difficulty, request.language)
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("message", "Error"))
    return MCQResponse(**result)


# ========== Question Bank Endpoints ==========

@app.get("/bank", response_model=List[MCQItem])
async def get_all_mcqs():
    """Return all MCQs in the bank."""
    return load_bank()


@app.post("/bank/add")
async def add_mcq_to_bank(mcq: MCQItem):
    """Add a single MCQ to the bank."""
    add_mcq(mcq.dict())
    return {"message": "MCQ added successfully", "total": len(load_bank())}


@app.post("/bank/search")
async def search_mcq_bank(query: str, top_k: int = 3):
    """Search the MCQ bank and return top matches."""
    results = search_bank(query, top_k)
    return {"query": query, "results": results}