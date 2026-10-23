# Architecture

## Components

| Component | Responsibility | Source |
|---|---|---|
| Log simulator | Generates synthetic login events and submits them over HTTP | `simulator.py` |
| REST API | Receives log lines, returns alert history and CSV exports | `backend/app/main.py` |
| Parser | Validates and converts log lines into structured events | `backend/app/parser.py` |
| Detection engine | Applies in-memory correlation rules and severity thresholds | `backend/app/analyzer.py` |
| Persistence | Stores generated alerts in SQLite through SQLAlchemy | `backend/app/database.py`, `models.py` |
| WebSocket manager | Broadcasts new alerts to connected dashboard clients | `backend/app/main.py` |
| Dashboard | Renders alerts and provides filtering/search | `frontend/index.html`, `frontend/script.js` |

## Event lifecycle

1. The simulator submits `{"log_line": "..."}` to `POST /api/logs`.
2. The parser validates timestamp, event type, username, and IP address.
3. The analyzer applies threshold/time-window rules and suppresses repeated identical alert keys during the cooldown.
4. Generated alerts are inserted into SQLite.
5. New alert payloads are returned by the API and broadcast to connected WebSocket clients.
6. The dashboard loads recent history through `GET /api/alerts` and appends live notifications.

## Persistence versus detection state

Alerts persist in SQLite. The recent failed-login window and alert cooldown are held in backend process memory. Restarting the backend therefore clears detection/cooldown state but does not delete the SQLite alert history.

## Deployment topology

Docker Compose defines a backend on loopback port `8000` and an Nginx-served frontend on loopback port `3000`. SQLite data is stored in the named `secpulse_data` volume. The frontend derives the API and WebSocket host from the host used to open the page.

## Local-demo security boundaries

The API does not implement authentication, authorization, rate limiting, TLS termination, durable detection state, or a production incident lifecycle. Use only synthetic log events and do not expose it to untrusted networks.
