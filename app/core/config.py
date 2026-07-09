from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://ruby:ruby_secret@db:5432/forro_ruby"
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440
    seed_default_password: str = "forroruby2026"
    cors_origins: str = "http://localhost:4200,http://127.0.0.1:4200"

    # IA (geração de ideias de conteúdo)
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-opus-4-8"

    # Regras de negócio
    daily_goal_minutes: int = 90       # meta diária de trabalho/estudo (1h30)
    alert_warning_hours: int = 48      # alerta amarelo: prazo em até 48h
    alert_urgent_hours: int = 24       # alerta vermelho: prazo em até 24h

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
