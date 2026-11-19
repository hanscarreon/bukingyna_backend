import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(UTC)


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True, index=True)
    phone_e164: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True, index=True)
    role: Mapped[str] = mapped_column(String(64), default="customer")  # customer | super_admin | client_admin | client_sub_admin
    tier: Mapped[str] = mapped_column(String(32), default="silver")  # silver | gold | platinum
    tenant_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    pin_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    login_failures: Mapped[int] = mapped_column(Integer, default=0)
    otp_failures: Mapped[int] = mapped_column(Integer, default=0)
    pin_failures: Mapped[int] = mapped_column(Integer, default=0)
    otp_blocked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    pin_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    active_session_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class OtpChallenge(Base):
    __tablename__ = "otp_challenges"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    phone_e164: Mapped[str] = mapped_column(String(20), index=True)
    code_hash: Mapped[str] = mapped_column(String(255))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    consumed: Mapped[bool] = mapped_column(Boolean, default=False)


class NotificationStub(Base):
    """Outbound notify stub — push/email/SMS delivery later."""

    __tablename__ = "notification_stubs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    channel: Mapped[str] = mapped_column(String(32))  # push | email | sms
    target: Mapped[str] = mapped_column(String(255))
    payload: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
