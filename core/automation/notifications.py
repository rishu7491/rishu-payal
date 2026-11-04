"""Notification and Alert Hub for Payal Automation Engine."""

import time
from typing import Callable, Dict, List, Optional

from .models import Notification, NotificationSeverity


class NotificationHub:
    """Dispatches and tracks notifications across task lifecycle and proactive events."""

    def __init__(self, max_history: int = 100):
        self._notifications: List[Notification] = []
        self._max_history = max_history
        self._subscribers: List[Callable[[Notification], None]] = []

    def notify(
        self,
        type: str,
        title: str,
        message: str,
        severity: NotificationSeverity = NotificationSeverity.INFO,
        metadata: Optional[Dict] = None,
    ) -> Notification:
        """Create and publish a new notification."""
        notif = Notification(
            type=type,
            title=title,
            message=message,
            severity=severity,
            timestamp=time.time(),
            metadata=metadata or {},
        )
        self._notifications.insert(0, notif)
        if len(self._notifications) > self._max_history:
            self._notifications = self._notifications[:self._max_history]

        # Trigger subscriber callbacks
        for sub in self._subscribers:
            try:
                sub(notif)
            except Exception:
                pass

        return notif

    def list_notifications(
        self,
        unread_only: bool = False,
        limit: int = 50,
    ) -> List[Notification]:
        """List notifications with optional unread filter."""
        items = self._notifications
        if unread_only:
            items = [n for n in items if not n.read]
        return items[:limit]

    def mark_as_read(self, notif_id: str) -> bool:
        """Mark a notification as read."""
        for n in self._notifications:
            if n.id == notif_id:
                n.read = True
                return True
        return False

    def mark_all_as_read(self) -> int:
        """Mark all notifications as read."""
        count = 0
        for n in self._notifications:
            if not n.read:
                n.read = True
                count += 1
        return count

    def get_unread_count(self) -> int:
        return sum(1 for n in self._notifications if not n.read)

    def subscribe(self, callback: Callable[[Notification], None]) -> None:
        self._subscribers.append(callback)


# Global singleton notification hub
NOTIFICATION_HUB = NotificationHub()

