from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str = "sqlite+aiosqlite:///./agentos_bench.db"
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_TOPIC_EVAL_EVENTS: str = "eval-events"
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    HUGGINGFACE_API_KEY: str = ""
    DEFAULT_LLM_JUDGE_MODEL: str = "claude-sonnet-4-20250514"
    ENV: str = "dev"
    LOG_LEVEL: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
