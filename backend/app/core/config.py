from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=('.env', 'backend/.env'), extra='ignore')

    env: str = Field(default='local', validation_alias='ENV')
    cors_origins: str = Field(
        default='http://localhost:5173,http://localhost:3000',
        validation_alias='CORS_ORIGINS',
    )
    max_upload_mb: int = Field(default=50, validation_alias='MAX_UPLOAD_MB')
    openai_api_key: str | None = Field(default=None, validation_alias='OPENAI_API_KEY')
    openai_whisper_model: str = Field(default='whisper-1', validation_alias='OPENAI_WHISPER_MODEL')
    openai_timeout_sec: float = Field(default=60.0, validation_alias='OPENAI_TIMEOUT_SEC')

    transcription_enabled: bool = Field(default=True, validation_alias='TRANSCRIPTION_ENABLED')
    transcription_cache_dir: str = Field(
        default='backend/.cache/transcripts',
        validation_alias='TRANSCRIPTION_CACHE_DIR',
    )
    transcription_max_calls_per_min: int = Field(
        default=3,
        validation_alias='TRANSCRIPTION_MAX_CALLS_PER_MIN',
    )

    summarization_enabled: bool = Field(default=True, validation_alias='SUMMARIZATION_ENABLED')
    openai_summarize_model: str = Field(default='gpt-5.4-mini', validation_alias='OPENAI_SUMMARIZE_MODEL')
    summarization_cache_dir: str = Field(
        default='backend/.cache/summaries',
        validation_alias='SUMMARIZATION_CACHE_DIR',
    )
    summarization_max_calls_per_min: int = Field(
        default=10,
        validation_alias='SUMMARIZATION_MAX_CALLS_PER_MIN',
    )

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(',') if o.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()

