from pydantic import BaseModel, Field
from typing import Optional, Dict


class AskRequest(BaseModel):
    question: str = Field(..., min_length=2)
    language: str = Field(default="en")
    mode: Optional[str] = Field(default=None)
    use_bank: bool = Field(default=False)


class AskResponse(BaseModel):
    answer: str
    language_used: str
    tokens_used: int
    status: str


class MCQRequest(BaseModel):
    topic: str = Field(..., min_length=2)
    difficulty: str = Field(default="medium")
    language: str = Field(default="en")


class MCQResponse(BaseModel):
    question: str
    options: Dict[str, str]
    correct: str
    explanation: str
    difficulty: str
    topic: str
    status: str = "success"