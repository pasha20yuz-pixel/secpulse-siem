from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LogLineRequest(BaseModel):
    log_line: str = Field(min_length=1, max_length=4096)


class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    alert_type: str
    severity: str
    username: str
    ip_address: str
    failed_attempts: int
    timestamp: datetime
