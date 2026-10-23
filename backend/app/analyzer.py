from datetime import datetime, timedelta
from typing import Dict, List, Tuple

from pydantic import BaseModel

from app.parser import SecurityEvent


class SecurityAlert(BaseModel):
    alert_type: str  # BRUTE_FORCE, PASSWORD_SPRAYING, SUSPICIOUS_SUCCESS
    severity: str  # HIGH, MEDIUM, LOW
    username: str
    ip_address: str
    failed_attempts: int
    timestamp: datetime


class SecurityAnalyzer:
    """Small in-memory heuristic analyzer for synthetic authentication events."""

    def __init__(
        self,
        threshold: int = 3,
        window_seconds: int = 60,
        alert_cooldown_seconds: int = 60,
    ):
        if threshold < 1:
            raise ValueError("threshold must be at least 1")
        if window_seconds < 1:
            raise ValueError("window_seconds must be at least 1")
        if alert_cooldown_seconds < 0:
            raise ValueError("alert_cooldown_seconds cannot be negative")

        self.threshold = threshold
        self.window = timedelta(seconds=window_seconds)
        self.alert_cooldown = timedelta(seconds=alert_cooldown_seconds)
        self.failed_logins: List[Dict] = []
        self._last_alert_at: Dict[Tuple[str, str, str], datetime] = {}

    @staticmethod
    def _calculate_severity(attempts: int) -> str:
        if attempts >= 10:
            return "HIGH"
        if attempts >= 6:
            return "MEDIUM"
        return "LOW"

    def _append_unless_suppressed(
        self, alerts: List[SecurityAlert], alert: SecurityAlert
    ) -> None:
        """Suppress repeated alerts with the same rule/user/IP during cooldown."""
        key = (alert.alert_type, alert.username, alert.ip_address)
        last_emitted = self._last_alert_at.get(key)
        if last_emitted is not None and alert.timestamp - last_emitted < self.alert_cooldown:
            return
        alerts.append(alert)
        self._last_alert_at[key] = alert.timestamp

    def process_event(self, event: SecurityEvent) -> List[SecurityAlert]:
        alerts: List[SecurityAlert] = []
        now = event.timestamp

        # Ignore future-dated entries when the event timestamps are out of order.
        self.failed_logins = [
            item
            for item in self.failed_logins
            if timedelta(0) <= now - item["timestamp"] <= self.window
        ]

        # Bound the cooldown map to keys seen recently. This is still in-memory
        # state and intentionally resets when the process restarts.
        max_age = max(self.window, self.alert_cooldown)
        self._last_alert_at = {
            key: timestamp
            for key, timestamp in self._last_alert_at.items()
            if now - timestamp <= max_age
        }

        if event.event_type == "LOGIN_FAILED":
            self.failed_logins.append(
                {
                    "timestamp": now,
                    "username": event.username,
                    "ip_address": event.ip_address,
                }
            )

            user_ip_fails = [
                item
                for item in self.failed_logins
                if item["username"] == event.username
                and item["ip_address"] == event.ip_address
            ]
            if len(user_ip_fails) >= self.threshold:
                attempts = len(user_ip_fails)
                self._append_unless_suppressed(
                    alerts,
                    SecurityAlert(
                        alert_type="BRUTE_FORCE",
                        severity=self._calculate_severity(attempts),
                        username=event.username,
                        ip_address=event.ip_address,
                        failed_attempts=attempts,
                        timestamp=now,
                    ),
                )

            ip_fails = [
                item
                for item in self.failed_logins
                if item["ip_address"] == event.ip_address
            ]
            unique_users = {item["username"] for item in ip_fails}
            if len(unique_users) >= self.threshold:
                attempts = len(ip_fails)
                self._append_unless_suppressed(
                    alerts,
                    SecurityAlert(
                        alert_type="PASSWORD_SPRAYING",
                        severity=self._calculate_severity(attempts),
                        username="*",
                        ip_address=event.ip_address,
                        failed_attempts=attempts,
                        timestamp=now,
                    ),
                )

        elif event.event_type == "LOGIN_SUCCESS":
            recent_fails = [
                item
                for item in self.failed_logins
                if item["username"] == event.username
                and item["ip_address"] == event.ip_address
            ]
            if len(recent_fails) >= self.threshold:
                self._append_unless_suppressed(
                    alerts,
                    SecurityAlert(
                        alert_type="SUSPICIOUS_SUCCESS",
                        severity="HIGH",
                        username=event.username,
                        ip_address=event.ip_address,
                        failed_attempts=len(recent_fails),
                        timestamp=now,
                    ),
                )

        return alerts
