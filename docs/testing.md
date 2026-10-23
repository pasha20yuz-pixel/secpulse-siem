# Testing and verification

## Automated tests

The test suite includes parser validation, three detection patterns, time-window expiry, duplicate-alert suppression, and an API integration test covering malformed input, alert persistence, CSV encoding, and WebSocket delivery using FastAPI's test client.

Run from the repository root:

```powershell
python -m pip install -r requirements.txt
python -m pytest -v
```

The API test uses an isolated temporary SQLite database so it does not modify `backend/secpulse.db` on the developer's machine.

## Verification in the preparation environment

The release candidate was checked with the following results in the preparation environment (Python 3.13.5; FastAPI 0.128.2; Pydantic 2.13.5; SQLAlchemy 2.0.50). Re-run the suite in the target Windows/Python 3.11 environment before publishing:

| Check | Result | Evidence / scope |
|---|---|---|
| Automated suite | Passed | 13 tests passed after the API integration test was included (current preparation environment) |
| API integration coverage | Passed | Root endpoint, malformed input, threshold alert, history, CSV BOM/content, WebSocket alert delivery |
| Pinned Windows dependency set | Not verified here | Run the commands above on Python 3.11 before publication |
| Browser rendering on Windows | Not verified here | Verify manually on the target PC |
| Docker container startup | Not verified here | Docker was not available in the preparation environment; the user's earlier `docker compose config` only validated the original config |
| Persistence across backend restart | Requires local check | SQLite file should remain while detection state resets |

## Manual release checklist

1. Run `python -m pytest -v` from a clean environment.
2. Start the API and open `http://127.0.0.1:8000/docs`.
3. Start the simulator and confirm that alerts appear in the API history.
4. Open `http://127.0.0.1:3000` through Docker Compose and verify WebSocket status, dashboard table, filters, search, and CSV download.
5. Restart only the backend and check that stored alerts remain while in-memory correlation state resets.
6. Before making the repository public, inspect the staged file list and confirm that `.venv`, SQLite files, `.env` files, credentials, real logs, and personal data are not included.

Only claim the checks that have actually been run for the exact commit being published.
