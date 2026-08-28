import httpx
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Service, Check, Incident
from app.config import settings


async def check_service(session: AsyncSession, service_id: int) -> None:
    """
    Проверка одного сервиса.
    - Делает HTTP GET запрос с таймаутом
    - Записывает результат в checks
    - Открывает/закрывает инциденты
    """
    # Получаем сервис из БД
    result = await session.execute(select(Service).where(Service.id == service_id))
    service = result.scalar_one_or_none()
    
    if not service or not service.is_active:
        return
    
    ok = False
    http_status = None
    latency_ms = None
    reason = None
    
    try:
        async with httpx.AsyncClient(timeout=settings.CHECK_TIMEOUT_SECONDS) as client:
            start = datetime.utcnow()
            response = await client.get(service.url)
            end = datetime.utcnow()
            
            http_status = response.status_code
            latency_ms = int((end - start).total_seconds() * 1000)
            ok = (response.status_code == service.expected_status)
            
    except httpx.TimeoutException:
        reason = "timeout"
    except httpx.RequestError as e:
        reason = str(e)
    except Exception as e:
        reason = f"unexpected error: {e}"
    
    # Записываем результат проверки
    check = Check(
        service_id=service.id,
        ok=ok,
        http_status=http_status,
        latency_ms=latency_ms,
    )
    session.add(check)
    
    # Логика инцидентов
    if not ok:
        # Проверяем, есть ли открытый инцидент
        result = await session.execute(
            select(Incident)
            .where(Incident.service_id == service.id)
            .where(Incident.ended_at.is_(None))
        )
        existing_incident = result.scalar_one_or_none()
        
        if not existing_incident:
            # Открываем новый инцидент
            incident = Incident(
                service_id=service.id,
                reason=reason or f"http status {http_status}",
            )
            session.add(incident)
    else:
        # Сервис работает — закрываем открытый инцидент если есть
        result = await session.execute(
            select(Incident)
            .where(Incident.service_id == service.id)
            .where(Incident.ended_at.is_(None))
        )
        existing_incident = result.scalar_one_or_none()
        
        if existing_incident:
            existing_incident.ended_at = datetime.utcnow()
    
    await session.commit()


async def check_all_services(session: AsyncSession) -> None:
    """Проверка всех активных сервисов."""
    result = await session.execute(select(Service).where(Service.is_active == True))
    services = result.scalars().all()
    
    for service in services:
        await check_service(session, service.id)
