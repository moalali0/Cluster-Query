from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_database_url: str = "postgresql://contract_ai_app:contract_ai_app@localhost:5432/contract_ai"
    ingest_database_url: str = "postgresql://contract_ai_ingest:contract_ai_ingest@localhost:5432/contract_ai"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    similarity_threshold: float = 0.62
    default_top_k: int = 5
    allowed_clients: str = "Bank_A,Bank_B"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def allowed_client_list(self) -> list[str]:
        return [c.strip() for c in self.allowed_clients.split(",") if c.strip()]


settings = Settings()
