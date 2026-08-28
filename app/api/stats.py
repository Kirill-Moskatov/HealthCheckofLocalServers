"""API endpoints для статистики."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta

from app.db import get_db
from app.models import Service, Check, Incident

router = APIRouter(prefix="/api", tags=["stats"])


@router.get("/stats")
async def get_stats(
    weeks: int = Query(default=10, ge=1, le=52),
    session: AsyncSession = Depends(get_db)
):
    """
    Получить статистику аптайма за N недель.
    Возвращает данные по каждому сервису: % доступности, сумма простоев, количество инцидентов.
    """
    result = await session.execute(select(Service))
    services = result.scalars().all()
    
    now = datetime.utcnow()
    start_date = now - timedelta(weeks=weeks)
    
    response = []
    for service in services:
        # Все инциденты сервиса за период
        incident_result = await session.execute(
            select(Incident)
            .where(Incident.service_id == service.id)
            .where(Incident.started_at >= start_date)
        )
        incidents = incident_result.scalars().all()
        
        total_downtime_seconds = 0
        incident_count = 0
        
        for incident in incidents:
            incident_count += 1
            
            # Рассчитываем длительность инцидента в рамках периода
            started = max(incident.started_at, start_date)
            ended = incident.ended_at if incident.ended_at else now
            
            # Если инцидент начался до периода и закончился до периода — пропускаем
            if ended < start_date:
                continue
            
            duration = (ended - started).total_seconds()
            total_downtime_seconds += duration
        
        # Общий период в секундах
        period_seconds = (now - start_date).total_seconds()
        
        # Аптайм в процентах
        uptime_percent = ((period_seconds - total_downtime_seconds) / period_seconds * 100) if period_seconds > 0 else 100
        uptime_percent = max(0, min(100, uptime_percent))
        
        response.append({
            "service_id": service.id,
            "service_name": service.name,
            "weeks": weeks,
            "uptime_percent": round(uptime_percent, 2),
            "total_downtime_seconds": int(total_downtime_seconds),
            "incident_count": incident_count,
        })
    
    return response


@router.get("/incidents")
async def get_all_incidents(limit: int = 100, session: AsyncSession = Depends(get_db)):
    """Получить последние инциденты по всем сервисам."""
    result = await session.execute(
        select(Incident)
        .order_by(Incident.started_at.desc())
        .limit(limit)
    )
    incidents = result.scalars().all()
    
    response = []
    for incident in incidents:
        duration = None
        if incident.ended_at:
            duration = int((incident.ended_at - incident.started_at).total_seconds())
        
        response.append({
            "id": incident.id,
            "service_id": incident.service_id,
            "started_at": incident.started_at.isoformat(),
            "ended_at": incident.ended_at.isoformat() if incident.ended_at else None,
            "duration_seconds": duration,
            "reason": incident.reason,
        })
    
    return response
