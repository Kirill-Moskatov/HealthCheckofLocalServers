from datetime import datetime
from sqlalchemy import String, ForeignKey, Integer, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Service(Base):
    """Сервис для мониторинга."""

    __tablename__ = "services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(512), nullable=False)
    expected_status: Mapped[int] = mapped_column(Integer, default=200)
    check_interval: Mapped[int] = mapped_column(Integer, default=20)  # минуты
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    checks: Mapped[list["Check"]] = relationship(back_populates="service", cascade="all, delete-orphan")
    incidents: Mapped[list["Incident"]] = relationship(back_populates="service", cascade="all, delete-orphan")


class Check(Base):
    """Результат проверки сервиса."""

    __tablename__ = "checks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    service_id: Mapped[int] = mapped_column(Integer, ForeignKey("services.id"), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    ok: Mapped[bool] = mapped_column(Boolean, nullable=False)
    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    service: Mapped["Service"] = relationship(back_populates="checks")


class Incident(Base):
    """Инцидент (простой сервиса)."""

    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    service_id: Mapped[int] = mapped_column(Integer, ForeignKey("services.id"), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    service: Mapped["Service"] = relationship(back_populates="incidents")


class Notification(Base):
    """Лог отправленных уведомлений."""

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    notification_type: Mapped[str] = mapped_column(String(50), nullable=False)  # down/up/digest
    message: Mapped[str] = mapped_column(Text, nullable=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
