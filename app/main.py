from fastapi import FastAPI

from app.db import init_db
from app.config import settings

# Импорт моделей для регистрации метаданных
from app import models  # noqa: F401

app = FastAPI(title=settings.APP_NAME)


@app.on_event("startup")
async def startup():
    await init_db()


@app.get("/health")
async def health_check():
    """Health check самого Pulse."""
    return {"status": "ok"}
