from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv
from pydantic_settings import SettingsConfigDict
import json  # added

# Load environment variables from a .env file if present
load_dotenv()

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore")
    PROJECT_NAME: str = Field(default="Secure Task Tracker")
    DATABASE_URL: str = Field(default="postgresql+psycopg2://postgres:password@localhost:5432/secure_task_tracker")
    JWT_SECRET_KEY: str = Field(default="CHANGE_ME_SECRET")
    JWT_ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    ENV: str = Field(default="dev")
    # Raw string ("*", comma list, or JSON list). Parsed via allowed_origins property.
    ALLOWED_ORIGINS: str = Field(default="*")
    LOG_LEVEL: str = Field(default="info")

    @property
    def allowed_origins(self) -> list[str]:
        raw = (self.ALLOWED_ORIGINS or "").strip()
        if not raw or raw == "*":
            return ["*"]
        if raw.startswith("["):
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    return [str(x).strip() for x in parsed if str(x).strip()]
            except Exception:
                return ["*"]
        return [p.strip() for p in raw.split(",") if p.strip()]

@lru_cache
def get_settings() -> Settings:
    s = Settings()
    if s.ENV.lower() == "prod" and s.JWT_SECRET_KEY == "CHANGE_ME_SECRET":  # basic safeguard
        raise ValueError("In production you must set a strong JWT_SECRET_KEY")
    return s

settings = get_settings()
