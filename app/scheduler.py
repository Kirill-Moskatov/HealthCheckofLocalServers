from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import async_session_maker
from app.checker import check_all_services


async def scheduled_check():
    """Задача для APScheduler: проверка всех сервисов."""
    async with async_session_maker() as session:
        await check_all_services(session)


def init_scheduler(scheduler: AsyncIOScheduler) -> None:
    """Инициализация планировщика задач."""
    # Проверки каждые 20 минут
    scheduler.add_job(
        scheduled_check,
        trigger=IntervalTrigger(minutes=20),
        id="check_services",
        name="Check all services",
        replace_existing=True,
    )
    
    # Заглушка для недельного дайджеста (этап 3)
    # scheduler.add_job(
    #     weekly_digest_job,
    #     trigger='cron',
    #     day_of_week='mon',
    #     hour=9,
    #     id="weekly_digest",
    #     name="Weekly digest",
    # )
    
    # Заглушка для чистки истории (старше 3 месяцев)
    # scheduler.add_job(
    #     cleanup_old_data_job,
    #     trigger='cron',
    #     hour=3,
    #     minute=0,
    #     id="cleanup_old_data",
    #     name="Cleanup old data",
    # )
