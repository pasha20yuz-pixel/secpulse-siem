# SecPulse SIEM

**SecPulse SIEM** is an educational security-monitoring prototype built with Python, FastAPI, SQLAlchemy, SQLite, WebSocket, and a lightweight browser dashboard. It ingests synthetic authentication events, applies heuristic detection rules, stores generated alerts, and exports alert history as CSV.

> **Project status:** educational/portfolio prototype. It is not a production SIEM and should not be exposed to untrusted networks. Detection state is in memory, there is no user authentication, and additional operational hardening is required for real deployments.

## Features

- Parse supported authentication log lines.
- Detect repeated failed logins from one IP against one username (`BRUTE_FORCE`).
- Detect failed logins against multiple usernames from one IP (`PASSWORD_SPRAYING`).
- Flag a successful login after repeated failures from the same user and IP (`SUSPICIOUS_SUCCESS`).
- Apply a configurable-in-code threshold/window and suppress duplicate alerts during a cooldown.
- Persist alerts in SQLite.
- Provide REST endpoints for log ingestion, alert history, and CSV export.
- Broadcast new alerts over WebSocket to connected dashboard clients.
- Display alerts in a browser dashboard with simple filters and search.
- Run unit tests with pytest and the application through Docker Compose.

## Architecture

```text
Synthetic log / simulator
          |
          v
     POST /api/logs
          |
          v
        Parser ---> reject malformed input
          |
          v
   Detection analyzer
   |       |       |
   v       v       v
Brute    Password  Suspicious
force    spraying  successful login
          |
          v
   SQLite alert history
     |           |
     v           v
 GET /api/alerts  CSV export

 New alerts are also broadcast to connected clients through /ws.
```

## Supported input format

Each request to `POST /api/logs` contains a JSON object with a single `log_line` field. Example:

```json
{
  "log_line": "[2026-10-23 10:25:00] LOGIN_FAILED user=admin ip=192.168.1.100"
}
```

Supported event types are `LOGIN_FAILED` and `LOGIN_SUCCESS`. Timestamps must use `YYYY-MM-DD HH:MM:SS`, and the IP address must be syntactically valid IPv4 or IPv6. Invalid lines are rejected instead of being assigned a fabricated timestamp.

## Detection rules

Default parameters are a threshold of **3 events**, a **60-second** correlation window, and a **60-second** duplicate-alert cooldown.

| Rule | Condition | Alert type |
|---|---|---|
| Brute force | At least 3 failed logins for the same user and IP inside the window | `BRUTE_FORCE` |
| Password spraying | Failed logins from the same IP cover at least 3 distinct usernames inside the window | `PASSWORD_SPRAYING` |
| Suspicious success | A successful login follows at least 3 recent failures for the same username and IP | `SUSPICIOUS_SUCCESS` |

Severity for brute-force and password-spraying alerts is `LOW` for 3–5 counted attempts, `MEDIUM` for 6–9, and `HIGH` for 10 or more. `SUSPICIOUS_SUCCESS` is marked `HIGH`. These are demonstration heuristics, not validated detection policies.

## API endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | API status |
| `POST` | `/api/logs` | Submit one log line and return any newly generated alerts |
| `GET` | `/api/alerts` | Return the latest 50 persisted alerts |
| `GET` | `/api/export/csv` | Export stored alerts as semicolon-delimited UTF-8 CSV |
| `WS` | `/ws` | WebSocket endpoint for live alert notifications |

When the backend is running, interactive OpenAPI docs are available at <http://127.0.0.1:8000/docs>.

## Run locally on Windows (PowerShell)

Requires Python 3.11 and a working Git installation for development.

From the repository root:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

Open <http://127.0.0.1:8000/docs> to use the API. Keep the server terminal open. In a second PowerShell window, from the repository root, run the simulator:

```powershell
.\.venv\Scripts\python.exe .\simulator.py
```

Press `Ctrl+C` to stop the simulator. The local SQLite database is created at `backend/secpulse.db` and is intentionally excluded from Git.

## Run tests

From the repository root with the virtual environment activated:

```powershell
python -m pytest -v
```

The tests cover parser validation, brute-force detection, password spraying, suspicious successful login, expiry of old failures, and duplicate-alert suppression.

## Run with Docker Compose

Docker Desktop must be installed and running. From the repository root:

```powershell
docker compose config
docker compose up --build
```

Open the dashboard at <http://127.0.0.1:3000> and API docs at <http://127.0.0.1:8000/docs>. The database is stored in a named Docker volume. Stop the stack with `Ctrl+C`, then run `docker compose down` in another terminal if needed. `docker compose down -v` also deletes the database volume; use it only if you intentionally want to remove stored demo alerts.

## Repository layout

```text
.
├── backend/
│   ├── app/             # FastAPI API, parser, analyzer, ORM and schemas
│   └── tests/           # Automated unit tests
├── docs/                # Architecture, rules, test cases and review notes
├── frontend/            # Static dashboard
├── .github/workflows/   # Automated tests on GitHub Actions
├── Dockerfile
├── docker-compose.yml
├── pytest.ini
├── requirements.txt
└── simulator.py         # Synthetic authentication event generator
```

## Known limitations

- This is a learning/demo prototype, not a production SIEM.
- Recent failed-login correlation state and duplicate-alert cooldowns are kept in memory and reset when the backend restarts.
- The API has no authentication, authorization, rate limiting, durable audit trail, or retention policy.
- Detection rules are simple heuristics and can generate false positives or miss attacks.
- Tailwind CSS is loaded from a CDN, so the dashboard needs network access for its styling.
- The dashboard's “top IPs” summary counts displayed alert records, not raw authentication events.
- Validate deployment settings before exposing the service beyond localhost.

## Security and privacy

Use synthetic logs during development. Do not commit `.env` files, credentials, local databases, or real authentication logs. The Compose configuration binds exposed ports to loopback by default. Change those settings only after implementing the necessary authentication, TLS, network restrictions, monitoring, and data-handling controls.
