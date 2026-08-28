from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.db import init_db
from app.config import settings
from app.scheduler import init_scheduler

# Импорт моделей для регистрации метаданных
from app import models  # noqa: F401

# Импорт роутеров
from app.api.services import router as services_router
from app.api.stats import router as stats_router

app = FastAPI(title=settings.APP_NAME)
scheduler = AsyncIOScheduler()


@app.on_event("startup")
async def startup():
    await init_db()
    
    # Инициализация планировщика
    init_scheduler(scheduler)
    scheduler.start()


@app.on_event("shutdown")
async def shutdown():
    scheduler.shutdown()


@app.get("/health")
async def health_check():
    """Health check самого Pulse."""
    return {"status": "ok"}


# Подключение роутеров
app.include_router(services_router)
app.include_router(stats_router)


# Раздача статики дашборда
app.mount("/static", StaticFiles(directory="app/web"), name="static")


@app.get("/")
async def root():
    """Главная страница дашборда."""
    return FileResponse("app/web/index.html")
