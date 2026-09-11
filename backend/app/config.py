"""Application settings.

Every provider, credential, budget, and bound is configurable from the
environment. Nothing secret is ever defaulted to a working value.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

TutorProvider = Literal["authored", "nvidia", "fake"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False
    )

    app_env: Literal["development", "test", "production"] = "development"
    database_url: str = "postgresql+psycopg://quantum:quantum_local_only@localhost:5432/quantum"
    public_origin: str = "http://localhost:5173"
    extra_allowed_origins: str = ""
    session_secret: str = "development-only-not-a-production-secret"
    session_ttl_days: int = 30
    cookie_secure: bool = False

    tutor_provider: TutorProvider = "authored"
    tutor_usage_mode: Literal["internal_evaluation", "production"] = "internal_evaluation"
    nvidia_api_key: str = ""
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"
    nvidia_model: str = "nvidia/nemotron-3-super-120b-a12b"
    tutor_temperature: float = 1.0
    tutor_top_p: float = 0.95
    tutor_max_output_tokens: int = 1024
    tutor_timeout_seconds: float = 45.0
    tutor_requests_per_minute: int = 6
    tutor_global_concurrency: int = 2
    tutor_max_input_characters: int = 2000
    tutor_max_context_tokens: int = 6000

    simulation_max_operations: int = 100
    simulation_max_shots: int = 1024

    content_root: str = Field(default="", description="Overrides the repository content/ path")

    @field_validator("tutor_provider")
    @classmethod
    def _guard_fake(cls, value: TutorProvider, info) -> TutorProvider:
        env = info.data.get("app_env")
        if value == "fake" and env != "test":
            raise ValueError("TUTOR_PROVIDER=fake is only permitted when APP_ENV=test")
        return value

    @property
    def allowed_origins(self) -> list[str]:
        origins = [self.public_origin]
        origins.extend(
            origin.strip() for origin in self.extra_allowed_origins.split(",") if origin.strip()
        )
        return list(dict.fromkeys(origins))

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    def tutor_live_configured(self) -> bool:
        return self.tutor_provider == "nvidia" and bool(self.nvidia_api_key)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if settings.is_production:
        if settings.session_secret == "development-only-not-a-production-secret":
            raise RuntimeError("SESSION_SECRET must be set in production")
        if settings.tutor_provider == "fake":
            raise RuntimeError("the fake tutor provider is never allowed in production")
    return settings
