"""API endpoints для сервисов."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta

from app.db import get_db
from app.models import Service, Check, Incident
from app.checker import check_service

router = APIRouter(prefix="/api/services", tags=["services"])


@router.get("")
async def get_services(session: AsyncSession = Depends(get_db)):
    """Получить список всех сервисов с текущим статусом."""
    result = await session.execute(select(Service))
    services = result.scalars().all()
    
    response = []
    for service in services:
        # Последняя проверка
        check_result = await session.execute(
            select(Check)
            .where(Check.service_id == service.id)
            .order_by(Check.timestamp.desc())
            .limit(1)
        )
        last_check = check_result.scalar_one_or_none()
        
        # Текущий инцидент (если есть)
        incident_result = await session.execute(
            select(Incident)
            .where(Incident.service_id == service.id)
            .where(Incident.ended_at.is_(None))
        )
        active_incident = incident_result.scalar_one_or_none()
        
        current_downtime = None
        if active_incident:
            downtime_delta = datetime.utcnow() - active_incident.started_at
            current_downtime = int(downtime_delta.total_seconds())
        
        response.append({
            "id": service.id,
            "name": service.name,
            "url": service.url,
            "expected_status": service.expected_status,
            "is_active": service.is_active,
            "status": "up" if last_check and last_check.ok else ("down" if last_check and not last_check.ok else "unknown"),
            "last_check": last_check.timestamp.isoformat() if last_check else None,
            "last_http_status": last_check.http_status if last_check else None,
            "last_latency_ms": last_check.latency_ms if last_check else None,
            "current_downtime_seconds": current_downtime,
        })
    
    return response


@router.get("/{service_id}/checks")
async def get_service_checks(service_id: int, limit: int = 100, session: AsyncSession = Depends(get_db)):
    """Получить историю проверок сервиса."""
    result = await session.execute(
        select(Check)
        .where(Check.service_id == service_id)
        .order_by(Check.timestamp.desc())
        .limit(limit)
    )
    checks = result.scalars().all()
    
    return [
        {
            "id": check.id,
            "timestamp": check.timestamp.isoformat(),
            "ok": check.ok,
            "http_status": check.http_status,
            "latency_ms": check.latency_ms,
        }
        for check in checks
    ]


@router.post("/{service_id}/check")
async def trigger_manual_check(service_id: int, session: AsyncSession = Depends(get_db)):
    """Запустить ручную проверку сервиса."""
    # Проверяем существование сервиса
    result = await session.execute(select(Service).where(Service.id == service_id))
    service = result.scalar_one_or_none()
    
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    await check_service(session, service_id)
    
    return {"status": "check completed"}


@router.get("/{service_id}/incidents")
async def get_service_incidents(service_id: int, limit: int = 50, session: AsyncSession = Depends(get_db)):
    """Получить историю инцидентов сервиса."""
    result = await session.execute(
        select(Incident)
        .where(Incident.service_id == service_id)
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
            "started_at": incident.started_at.isoformat(),
            "ended_at": incident.ended_at.isoformat() if incident.ended_at else None,
            "duration_seconds": duration,
            "reason": incident.reason,
        })
    
    return response
