# v6 - chapter boost with clean indentation
import os, json
from openai import AsyncOpenAI
from app.core.config import settings
from app.core.prompts import get_prompt, get_output_instruction
import re

class AIService:
    _chunks = None

    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL
        )

    def _load_chunks_if_needed(self):
        if self._chunks is not None:
            return
        chunks_path = os.path.join("data", "ncert_index", "chunks.json")
        if os.path.exists(chunks_path):
            with open(chunks_path, "r", encoding="utf-8") as f:
                self._chunks = json.load(f)
            print(f"✅ Loaded {len(self._chunks)} text chunks for keyword search")
        else:
            self._chunks = []
            print("⚠️ chunks.json not found, NCERT search disabled")

    def search_ncert(self, query: str, top_k: int = 3) -> str:
        self._load_chunks_if_needed()
        if not self._chunks:
            return ""

        physics_topics = {
            "electrostatics", "current electricity", "magnetism", "electromagnetic induction",
            "alternating current", "electromagnetic waves", "optics", "ray optics", "wave optics",
            "dual nature", "atoms", "nuclei", "semiconductor", "electronic devices",
            "communication systems", "kinematics", "laws of motion", "work energy", "power",
            "rotational motion", "gravitation", "thermodynamics", "kinetic theory", "oscillations",
            "waves", "electric charges", "electric fields", "potential", "capacitance",
            "moving charges", "magnetism and matter", "photoelectric effect", "interference",
            "diffraction", "polarisation", "light", "mirror", "lens", "prism"
        }

        query_lower = query.lower()
        detected_topics = [topic for topic in physics_topics if topic in query_lower]

        stop_words = {"the", "is", "at", "which", "on", "and", "a", "an", "in", "of", "to", "for",
                      "with", "from", "by", "as", "or", "not", "this", "that", "it", "be", "has",
                      "have", "are", "was", "were", "been", "can", "could", "will", "would", "shall",
                      "should", "may", "might", "must", "i", "you", "he", "she", "we", "they", "me",
                      "him", "us", "them", "my", "your", "his", "her", "its", "our", "their", "give",
                      "question", "from", "board", "pyq", "cbse", "jee", "neet"}

        query_words = [w for w in query_lower.split() if w not in stop_words and len(w) > 2]
        if not query_words:
            query_words = query_lower.split()

        topic_keywords = {w for w in query_words if len(w) > 4}
        phrase = query_lower

        scored = []
        for chunk in self._chunks:
            lower_chunk = chunk.lower()
            base = sum(1 for word in query_words if word in lower_chunk)
            topic_boost = 3 * sum(1 for topic in topic_keywords if topic in lower_chunk)
            phrase_boost = 5 if phrase in lower_chunk else 0
            chapter_boost = 10 * sum(1 for topic in detected_topics if topic in lower_chunk)
            total = base + topic_boost + phrase_boost + chapter_boost
            if total > 0:
                scored.append((total, chunk))

        scored.sort(key=lambda x: x[0], reverse=True)
        top_chunks = [chunk for score, chunk in scored[:top_k]]
        return "\n\n".join(top_chunks)

    def format_physics_math(self, text: str) -> str:
        math_blocks = []
        def save_math(match):
            math_blocks.append(match.group(0))
            return f'<<<MATH{len(math_blocks)-1}>>>'
        text = re.sub(r'\$\$.*?\$\$|\$.*?\$', save_math, text, flags=re.DOTALL)
        text = re.sub(
            r'(^|\n)([a-zA-Z0-9]+\s*=\s*[a-zA-Z0-9\s\/\*\+\-\(\)\.]+)(\n|$)',
            r'\1$$\2$$\3', text
        )
        text = re.sub(
            r'(?<![a-zA-Z$])([a-zA-Z])(?![a-zA-Z$])',
            lambda m: f'${m.group(1)}$' if not m.group(0).startswith('<<<') else m.group(0),
            text
        )
        for i, block in enumerate(math_blocks):
            text = text.replace(f'<<<MATH{i}>>>', block)
        return text

    async def ask(self, question: str, language: str = "en", mode: str = None,
                  extra_context: str = "") -> dict:
        ncert_context = self.search_ncert(question)
        if ncert_context:
            ncert_context = (
                "Use the following NCERT/Board paper content to give a detailed answer:\n"
                + ncert_context + "\n\n"
            )

        full_question = question
        if extra_context:
            full_question = extra_context + ncert_context + "Student's question: " + question
        else:
            full_question = ncert_context + "Student's question: " + question

        system_prompt = get_prompt(language, "tutor")
        output_instruction = get_output_instruction(language)

        if mode == "derive":
            question = f"Provide a complete step-by-step derivation: {question}"
        elif mode == "solve":
            question = f"Solve this numerical problem with all steps: {question}"
        elif mode == "explain":
            question = f"Explain this concept clearly with examples: {question}"

        messages = [
            {"role": "system", "content": f"{system_prompt}\n\n{output_instruction}"},
            {"role": "user", "content": full_question}
        ]

        try:
            response = await self.client.chat.completions.create(
                model=settings.AI_MODEL,
                messages=messages,
                temperature=0.3,
                max_tokens=1500
            )
            raw_answer = response.choices[0].message.content
            formatted_answer = self.format_physics_math(raw_answer)
            return {
                "answer": formatted_answer,
                "language_used": language,
                "tokens_used": response.usage.total_tokens,
                "status": "success"
            }
        except Exception as e:
            return {
                "answer": f"Error: {str(e)}",
                "language_used": language,
                "tokens_used": 0,
                "status": "error"
            }

    async def generate_mcq(self, topic: str, difficulty: str = "medium", language: str = "en") -> dict:
        mcq_prompt = get_prompt(language, "mcq_generator")
        user_prompt = f"Topic: {topic}\nDifficulty: {difficulty}"
        try:
            response = await self.client.chat.completions.create(
                model=settings.AI_MODEL,
                messages=[
                    {"role": "system", "content": mcq_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=800
            )
            content = response.choices[0].message.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            mcq_data = json.loads(content.strip())
            mcq_data["status"] = "success"
            return mcq_data
        except json.JSONDecodeError:
            return {"status": "error", "message": "Failed to parse AI response"}
        except Exception as e:
            return {"status": "error", "message": str(e)}


ai_service = AIService()