from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Cloud platforms (Render, Railway) provide a single DATABASE_URL.
    # When set, it is used for both app and ingest connections.
    database_url: str = ""

    app_database_url: str = ""
    ingest_database_url: str = ""
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    similarity_threshold: float = 0.62
    default_top_k: int = 5
    allowed_clients: str = "Bank_A,Bank_B,Bank_C"

    # Ollama / LLM settings
    ollama_host: str = "http://host.docker.internal:11434"
    ollama_model: str = "llama3.2:latest"  # production: "llama3:8b-instruct"
    llm_enabled: bool = True
    llm_temperature: float = 0.1
    llm_max_tokens: int = 1024

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @model_validator(mode="after")
    def _resolve_db_urls(self):
        base = self.database_url
        # Render uses postgres://, psycopg3 expects postgresql://
        if base.startswith("postgres://"):
            base = "postgresql://" + base[len("postgres://"):]

        if not self.app_database_url:
            self.app_database_url = base or "postgresql://contract_ai_app:contract_ai_app@localhost:5432/contract_ai"
        if not self.ingest_database_url:
            self.ingest_database_url = base or "postgresql://contract_ai_ingest:contract_ai_ingest@localhost:5432/contract_ai"
        return self

    @property
    def allowed_client_list(self) -> list[str]:
        return [c.strip() for c in self.allowed_clients.split(",") if c.strip()]


settings = Settings()
