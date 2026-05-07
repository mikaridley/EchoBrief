from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    env: str = Field(default='local', validation_alias='ENV')
    cors_origins: str = Field(
        default='http://localhost:5173,http://localhost:3000',
        validation_alias='CORS_ORIGINS',
    )
    max_upload_mb: int = Field(default=50, validation_alias='MAX_UPLOAD_MB')

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(',') if o.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()

