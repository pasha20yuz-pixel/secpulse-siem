from sqlalchemy import Column, Integer, String, DateTime
from app.database import Base

class AlertModel(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_type = Column(String, index=True)
    severity = Column(String)
    username = Column(String)
    ip_address = Column(String)
    failed_attempts = Column(Integer)
    timestamp = Column(DateTime)
