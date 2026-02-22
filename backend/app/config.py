import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Gemini API
    gemini_api_key: str = ""

    # Vertex AI (project_id is read from the JSON file)
    vertex_ai_service_account_json: str = ""

    # App
    database_url: str = "sqlite+aiosqlite:///./data/creativeai.db"
    media_dir: str = "./media"
    cors_origins: str = "http://localhost:5173"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

# Ensure directories exist
os.makedirs(settings.media_dir, exist_ok=True)
os.makedirs("data", exist_ok=True)
