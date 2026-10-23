# Technical report: SecPulse SIEM

## 1. Project overview

SecPulse SIEM is an educational prototype for ingesting synthetic authentication events, applying heuristic detection rules, persisting generated alerts, and presenting them through a browser dashboard. It uses Python, FastAPI, SQLAlchemy, SQLite, WebSocket, HTML, JavaScript, and Tailwind CSS loaded from a CDN.

## 2. Objective

The project demonstrates a basic security-event processing path: raw authentication log line → parsing and validation → correlation rules → alert persistence → API history/CSV export and live WebSocket notification.

## 3. Functional scope

- Accept a log line through `POST /api/logs`.
- Parse supported event types, timestamp, username, and IPv4/IPv6 address.
- Detect brute-force-like behavior, password spraying, and successful logins following repeated failures.
- Assign heuristic severity and suppress repeated matching alerts during a cooldown.
- Persist generated alerts in SQLite.
- Expose alert history and CSV export endpoints.
- Broadcast new alerts to connected dashboard clients over `/ws`.
- Generate synthetic events for controlled demos.

## 4. Architecture

The simulator submits events to the REST API. The parser rejects malformed lines. The analyzer keeps recent failed events in process memory and applies three rules. Generated alerts are persisted through SQLAlchemy, returned in the HTTP response, and broadcast over WebSocket. The browser dashboard displays historical and live alerts.

Detailed design and known limits are documented in [architecture](../architecture.md), [detection rules](../detection-rules.md), and [limitations](../limitations.md).

## 5. Verification

The release candidate includes unit tests for parser validation and detection behavior, plus an API integration test covering request validation, threshold alert generation, alert history, CSV output, and WebSocket notification. Run `python -m pytest -v` to reproduce the results for the current checkout.

Browser rendering and Docker container startup must be verified on the target machine before describing those deployment paths as tested. The API integration test does not replace a manual dashboard test.

## 6. Limitations

This project is not production-ready. Detection and suppression state are kept in memory, authentication and authorization are absent, there is no rate limiting or retention policy, and detection rules are unvalidated heuristics. Use synthetic data and keep the development services bound to localhost.

## 7. Suggested evidence

After verifying a specific commit, capture genuine screenshots of:

- the dashboard showing live alerts;
- the simulator terminal showing submitted events and alerts;
- Swagger showing a successful request;
- the test suite passing.

Do not add mock or placeholder screenshots presented as actual test evidence.
