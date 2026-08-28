from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Настройки приложения Pulse."""

    # Приложение
    APP_NAME: str = "Pulse"
    DEBUG: bool = False

    # База данных
    DATABASE_URL: str = "sqlite+aiosqlite:///./pulse.db"

    # Проверки сервисов
    CHECK_INTERVAL_MINUTES: int = 20
    CHECK_TIMEOUT_SECONDS: int = 10

    # Уведомления (мок)
    MAX_BOT_TOKEN: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
