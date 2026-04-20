"""Application settings — single source of truth for all configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── App ──────────────────────────────────────────────────────────────
    app_name: str = "enterprise-agent-orchestrator"
    app_env: str = "dev"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"

    # ── Postgres ─────────────────────────────────────────────────────────
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "agent_db"
    postgres_user: str = "agent_user"
    postgres_password: str = "agent_pass"

    # ── Redis ────────────────────────────────────────────────────────────
    redis_host: str = "localhost"
    redis_port: int = 6379

    # ── Qdrant ───────────────────────────────────────────────────────────
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333

    # ── Langfuse ─────────────────────────────────────────────────────────
    langfuse_host: str = "http://localhost:3000"
    langfuse_public_key: str = "changeme"
    langfuse_secret_key: str = "changeme"

    # ── OpenAI ───────────────────────────────────────────────────────────
    openai_api_key: str = "changeme"
    openai_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"

    # ── Timeouts / Policies ──────────────────────────────────────────────
    request_timeout_seconds: int = 30
    tool_retry_attempts: int = 3
    tool_retry_delay_seconds: float = 1.0
    approval_timeout_seconds: int = 3600  # 1 hour

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def database_url_sync(self) -> str:
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}"

    @property
    def qdrant_url(self) -> str:
        return f"http://{self.qdrant_host}:{self.qdrant_port}"


settings = Settings()
