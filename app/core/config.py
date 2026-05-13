import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    APP_NAME: str = "Physics AI Assistant"
    VERSION: str = "1.0.0"
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com")
    AI_MODEL: str = os.getenv("AI_MODEL", "deepseek-chat")
    ACTIVE_LANGUAGES: list = ["en"]
    DEFAULT_LANGUAGE: str = "en"
    HOST: str = "127.0.0.1"
    PORT: int = 8000


settings = Settings()