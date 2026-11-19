"""Notification port — delivery blank for now; rows stored for later push/email/SMS."""

from typing import Protocol

from sqlalchemy.orm import Session

from app.features.auth.data.models import NotificationStub


class NotificationPort(Protocol):
    def notify(self, channel: str, target: str, payload: str) -> None: ...


class StubNotificationService:
    def __init__(self, db: Session) -> None:
        self._db = db

    def notify(self, channel: str, target: str, payload: str) -> None:
        self._db.add(NotificationStub(channel=channel, target=target, payload=payload))
        self._db.commit()
