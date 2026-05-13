import json
import os
from typing import List, Dict, Optional

# Path to your custom MCQ bank file
BANK_PATH = os.path.join("data", "question_bank", "custom_mcqs.json")


def load_bank() -> List[Dict]:
    """Load the question bank from JSON file. Returns list of MCQs."""
    if not os.path.exists(BANK_PATH):
        # Create an empty bank if not exists
        os.makedirs(os.path.dirname(BANK_PATH), exist_ok=True)
        with open(BANK_PATH, "w", encoding="utf-8") as f:
            json.dump([], f)
        return []
    with open(BANK_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_bank(mcqs: List[Dict]):
    """Save the entire question bank to JSON."""
    os.makedirs(os.path.dirname(BANK_PATH), exist_ok=True)
    with open(BANK_PATH, "w", encoding="utf-8") as f:
        json.dump(mcqs, f, indent=2, ensure_ascii=False)


def add_mcq(mcq: Dict):
    """Add a single MCQ to the bank."""
    mcqs = load_bank()
    mcqs.append(mcq)
    save_bank(mcqs)


def search_bank(query: str, top_k: int = 3) -> List[Dict]:
    """
    Simple keyword-based search.
    Returns the top_k MCQs whose question/explanation/topic contains the query words.
    This is a basic fallback – you can later replace it with vector search.
    """
    mcqs = load_bank()
    query_words = query.lower().split()
    scored = []
    for mcq in mcqs:
        text = (mcq.get("question", "") + " " + mcq.get("explanation", "") + " " + mcq.get("topic", "")).lower()
        score = sum(1 for word in query_words if word in text)
        if score > 0:
            scored.append((score, mcq))
    # Sort by score descending
    scored.sort(key=lambda x: x[0], reverse=True)
    return [mcq for score, mcq in scored[:top_k]]