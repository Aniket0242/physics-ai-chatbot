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
    """Search the question bank across all relevant fields."""
    mcqs = load_bank()
    query_words = query.lower().split()
    scored = []
    for item in mcqs:
        # Combine all searchable text
        text_parts = [
            item.get("question", ""),
            item.get("explanation", ""),
            item.get("answer", ""),
            item.get("topic", ""),
            item.get("figure_description", ""),
            str(item.get("year", "")),
            item.get("set_type", ""),
            str(item.get("marks", ""))
        ]
        combined = " ".join(text_parts).lower()
        score = sum(1 for word in query_words if word in combined)
        if score > 0:
            scored.append((score, item))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for score, item in scored[:top_k]]