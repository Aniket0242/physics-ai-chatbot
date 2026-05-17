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


# MCQ Item model for question bank (kept for API compatibility)
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
    bank_context = ""
    if request.use_bank:
        results = search_bank(request.question, top_k=3)
        if results:
            # Mandatory directive to force AI to use bank questions
            bank_context = (
                "IMPORTANT: You MUST answer using ONLY the following questions from the student's personal bank. "
                "Choose the most relevant one and present it EXACTLY as given, including all options, the correct answer, and the explanation. "
                "Do NOT add any extra information or use your own knowledge.\n\n"
                "Here are the questions:\n"
            )
            for i, item in enumerate(results, 1):
                if item.get("type") == "mcq":
                    bank_context += (
                        f"{i}. [MCQ] {item['question']}\n"
                        f"   Options: {item['options']}\n"
                        f"   Correct: {item['correct']}\n"
                        f"   Explanation: {item['explanation']}\n"
                    )
                else:
                    q_type = item.get("type", "short").capitalize()
                    bank_context += (
                        f"{i}. [{q_type}] {item['question']}\n"
                        f"   Answer: {item.get('answer', '')}\n"
                    )
                # Include year/set info if available
                if item.get("year"):
                    bank_context += f"   Year: {item['year']}\n"
                if item.get("set_type"):
                    bank_context += f"   Set: {item['set_type']}\n"
                if item.get("marks"):
                    bank_context += f"   Marks: {item['marks']}\n"
                if item.get("figure_description"):
                    bank_context += f"   Figure description: {item['figure_description']}\n"
                bank_context += "\n"
            bank_context += "End of bank questions. Remember: you MUST answer with one of them exactly as provided.\n\n"

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