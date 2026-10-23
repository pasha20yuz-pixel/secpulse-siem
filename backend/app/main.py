import csv
import io
import json
import logging
import os
from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.analyzer import SecurityAnalyzer
from app.database import Base, engine, get_db
from app.models import AlertModel
from app.parser import parse_log_line
from app.schemas import AlertResponse, LogLineRequest

logger = logging.getLogger(__name__)

# Create the SQLite table(s) if this is a fresh local run.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="SecPulse SIEM API", version="1.0.0")

# This is a local demo. Add any intentional dashboard origin explicitly rather
# than allowing arbitrary websites to call the API.
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "SECPULSE_CORS_ORIGINS",
        "http://127.0.0.1:3000,http://localhost:3000,"
        "http://127.0.0.1:8000,http://localhost:8000",
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Accept"],
)

analyzer = SecurityAnalyzer(threshold=3, window_seconds=60, alert_cooldown_seconds=60)


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict) -> None:
        stale_connections = []
        payload = json.dumps(message, default=str)
        for connection in list(self.active_connections):
            try:
                await connection.send_text(payload)
            except Exception:
                # A broken client should not prevent the alert from being
                # returned by the API or delivered to other clients.
                logger.debug("Removing stale WebSocket connection", exc_info=True)
                stale_connections.append(connection)
        for connection in stale_connections:
            self.disconnect(connection)


manager = ConnectionManager()


@app.get("/")
def read_root():
    return {"status": "SecPulse SIEM Engine is running", "timestamp": datetime.now()}


@app.post("/api/logs", response_model=list[AlertResponse])
async def ingest_log(data: LogLineRequest, db: Session = Depends(get_db)):
    """Parse and analyze one synthetic authentication log line."""
    event = parse_log_line(data.log_line)
    if event is None:
        raise HTTPException(status_code=400, detail="Invalid log format, event type, timestamp, or IP address")

    triggered_alerts = analyzer.process_event(event)
    response_alerts = []
    for alert in triggered_alerts:
        db_alert = AlertModel(
            alert_type=alert.alert_type,
            severity=alert.severity,
            username=alert.username,
            ip_address=alert.ip_address,
            failed_attempts=alert.failed_attempts,
            timestamp=alert.timestamp,
        )
        db.add(db_alert)
        db.commit()
        db.refresh(db_alert)

        alert_data = {
            "alert_type": alert.alert_type,
            "severity": alert.severity,
            "username": alert.username,
            "ip_address": alert.ip_address,
            "failed_attempts": alert.failed_attempts,
            "timestamp": str(alert.timestamp),
        }
        response_alerts.append(alert_data)
        await manager.broadcast(alert_data)

    return response_alerts


@app.get("/api/alerts", response_model=list[AlertResponse])
def get_historical_alerts(db: Session = Depends(get_db)):
    """Return the latest 50 persisted alerts."""
    return db.query(AlertModel).order_by(AlertModel.id.desc()).limit(50).all()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Accept dashboard clients and broadcast newly generated alerts."""
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.get("/api/export/csv")
def export_alerts_csv(db: Session = Depends(get_db)):
    """Export all persisted alerts as a semicolon-delimited UTF-8 CSV."""
    alerts = db.query(AlertModel).order_by(AlertModel.timestamp.desc()).all()

    output = io.StringIO(newline="")
    writer = csv.writer(output, delimiter=";")
    writer.writerow(
        ["ID", "Timestamp", "Alert Type", "Severity", "Username", "IP Address", "Failed Attempts"]
    )
    for alert in alerts:
        writer.writerow(
            [
                alert.id,
                alert.timestamp.strftime("%Y-%m-%d %H:%M:%S") if alert.timestamp else "N/A",
                alert.alert_type,
                alert.severity,
                alert.username,
                alert.ip_address,
                alert.failed_attempts,
            ]
        )

    # Encode once with a BOM so Excel detects UTF-8; avoid a double BOM.
    csv_data = output.getvalue().encode("utf-8-sig")
    return StreamingResponse(
        iter([csv_data]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=secpulse_security_report.csv"},
    )
