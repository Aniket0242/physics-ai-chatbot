from openai import AsyncOpenAI
from app.core.config import settings
from app.core.prompts import get_prompt, get_output_instruction
import json
import re


class AIService:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL
        )

    def format_physics_math(self, text: str) -> str:
        math_blocks = []
        def save_math(match):
            math_blocks.append(match.group(0))
            return f'<<<MATH{len(math_blocks)-1}>>>'
        text = re.sub(r'\$\$.*?\$\$|\$.*?\$', save_math, text, flags=re.DOTALL)
        text = re.sub(
            r'(^|\n)([a-zA-Z0-9]+\s*=\s*[a-zA-Z0-9\s\/\*\+\-\(\)\.]+)(\n|$)',
            r'\1$$\2$$\3',
            text
        )
        text = re.sub(
            r'(?<![a-zA-Z$])([a-zA-Z])(?![a-zA-Z$])',
            lambda m: f'${m.group(1)}$' if not m.group(0).startswith('<<<') else m.group(0),
            text
        )
        for i, block in enumerate(math_blocks):
            text = text.replace(f'<<<MATH{i}>>>', block)
        return text

    async def ask(self, question: str, language: str = "en", mode: str = None, extra_context: str = "") -> dict:
        system_prompt = get_prompt(language, "tutor")
        output_instruction = get_output_instruction(language)

        if mode == "derive":
            question = f"Provide a complete step-by-step derivation: {question}"
        elif mode == "solve":
            question = f"Solve this numerical problem with all steps: {question}"
        elif mode == "explain":
            question = f"Explain this concept clearly with examples: {question}"

        # Prepend extra context (from question bank) to the question
        full_question = question
        if extra_context:
            full_question = extra_context + "Student's question: " + question

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