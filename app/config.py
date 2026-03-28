from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5442/boilerworks"
    redis_url: str = "redis://localhost:6385/0"
    secret_key: str = "change-me-in-production"
    session_cookie_name: str = "session_token"
    session_max_age: int = 86400 * 7  # 7 days
    debug: bool = False

    model_config = {"env_prefix": "", "case_sensitive": False}


settings = Settings()
