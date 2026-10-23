import ipaddress
import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SecurityEvent(BaseModel):
    timestamp: datetime
    event_type: str  # LOGIN_SUCCESS or LOGIN_FAILED
    username: str
    ip_address: str


_LOG_PATTERN = re.compile(
    r"\[(?P<timestamp>[^\]]+)\]\s+"
    r"(?P<event_type>LOGIN_SUCCESS|LOGIN_FAILED)\s+"
    r"user=(?P<username>\S+)\s+"
    r"ip=(?P<ip_address>\S+)"
)
_SUPPORTED_EVENTS = {"LOGIN_SUCCESS", "LOGIN_FAILED"}


def parse_log_line(log_line: str) -> Optional[SecurityEvent]:
    """Parse one supported authentication log line; reject invalid input.

    Expected example:
    [2026-10-12 12:00:00] LOGIN_FAILED user=admin ip=192.168.1.50
    """
    if not isinstance(log_line, str):
        return None

    match = _LOG_PATTERN.fullmatch(log_line.strip())
    if match is None:
        return None

    values = match.groupdict()
    if values["event_type"] not in _SUPPORTED_EVENTS:
        return None

    try:
        timestamp = datetime.strptime(values["timestamp"], "%Y-%m-%d %H:%M:%S")
        ipaddress.ip_address(values["ip_address"])
    except ValueError:
        return None

    return SecurityEvent(
        timestamp=timestamp,
        event_type=values["event_type"],
        username=values["username"],
        ip_address=values["ip_address"],
    )
