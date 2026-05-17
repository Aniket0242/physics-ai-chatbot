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
    """Search the question bank with smart boosting for year, type, and set."""
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
            item.get("type", ""),
            str(item.get("marks", ""))
        ]
        combined = " ".join(text_parts).lower()
        
        # Base score: number of matching words
        base = sum(1 for word in query_words if word in combined)
        
        # Boost: if query mentions the exact year, add 10
        year_boost = 10 if str(item.get("year")) in query_words else 0
        
        # Boost: if query mentions the type (mcq, short, long)
        type_boost = 5 if item.get("type", "") in query_words else 0
        
        # Boost: if query mentions the set_type (regular/visually_impaired)
        set_boost = 5 if item.get("set_type", "") in query_words else 0
        
        total = base + year_boost + type_boost + set_boost
        if total > 0:
            scored.append((total, item))
    
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for score, item in scored[:top_k]]