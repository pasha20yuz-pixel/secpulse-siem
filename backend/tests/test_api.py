import os
import tempfile
from pathlib import Path

# Isolate API tests from a developer's local database before importing app.main.
_TEST_DB_DIR = tempfile.TemporaryDirectory(prefix="secpulse-api-tests-")
os.environ["SECPULSE_DB_PATH"] = str(Path(_TEST_DB_DIR.name) / "api-test.db")

from fastapi.testclient import TestClient

from app.main import Base, analyzer, app, engine


def test_api_ingestion_history_csv_and_websocket():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    analyzer.failed_logins.clear()
    analyzer._last_alert_at.clear()

    try:
        with TestClient(app) as client:
            assert client.get("/").status_code == 200
            assert client.post("/api/logs", json={"log_line": "not a log"}).status_code == 400

            with client.websocket_connect("/ws") as websocket:
                responses = []
                for second in range(3):
                    response = client.post(
                        "/api/logs",
                        json={
                            "log_line": (
                                f"[2026-10-23 10:00:0{second}] "
                                "LOGIN_FAILED user=admin ip=192.0.2.10"
                            )
                        },
                    )
                    assert response.status_code == 200
                    responses.append(response.json())

                assert responses[0] == []
                assert responses[1] == []
                assert responses[2][0]["alert_type"] == "BRUTE_FORCE"
                pushed_alert = websocket.receive_json()
                assert pushed_alert["alert_type"] == "BRUTE_FORCE"
                assert pushed_alert["username"] == "admin"

            history = client.get("/api/alerts")
            assert history.status_code == 200
            assert len(history.json()) == 1
            assert history.json()[0]["alert_type"] == "BRUTE_FORCE"

            csv_response = client.get("/api/export/csv")
            assert csv_response.status_code == 200
            assert csv_response.headers["content-type"].startswith("text/csv")
            assert csv_response.content.startswith(b"\xef\xbb\xbf")
            assert csv_response.content.count(b"\xef\xbb\xbf") == 1
            assert b"Alert Type" in csv_response.content
            assert b"BRUTE_FORCE" in csv_response.content
    finally:
        engine.dispose()
        _TEST_DB_DIR.cleanup()
