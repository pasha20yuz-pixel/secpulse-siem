# Known limitations and security review

SecPulse SIEM is an educational portfolio prototype, not a production security monitoring system.

## Security boundaries

- The API has no authentication or authorization. Anyone who can reach it can submit events and read/export alert history.
- CORS is restricted to the local dashboard/API origins by default; update `SECPULSE_CORS_ORIGINS` deliberately if a different deployment is required.
- Docker Compose binds host ports to `127.0.0.1` by default. Do not widen that binding without appropriate network and application controls.
- HTTPS/TLS is not configured by the Compose stack.
- Tailwind CSS is loaded from a CDN; dashboard styling requires network access.
- Only synthetic events should be used in the public demo. Do not publish sensitive logs, credentials, or local database files.

## Detection and reliability

- Failed-login correlation and alert cooldown state are in memory and reset on backend restart.
- Detection uses simple threshold/time-window heuristics and has not been evaluated against real-world telemetry.
- The system has no rate limiting, durable incident lifecycle, retention policy, or authentication.
- The parser validates the event type, timestamp format, and IP syntax, but usernames are not normalized.
- Out-of-order and clock-skewed events are handled only simplistically.
- Password spraying reports a total event count even though the rule threshold is based on distinct usernames.
- The dashboard top-IP widget counts alert records loaded by the browser, not raw source events.
- Multi-client WebSocket delivery is best-effort; this project does not implement a durable message queue.

## Packaging

- `.venv`, generated caches, local logs, and local SQLite databases are excluded from the repository.
- Docker Compose uses a named volume for the database so a clean checkout does not require a pre-created local database file.
- `requests` is declared for the simulator.
