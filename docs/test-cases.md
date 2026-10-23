# Test cases

Use synthetic data only. Record commit hash, environment, command, expected result, actual result, and pass/fail status for manual checks.

| ID | Area | Input / action | Expected result | Status |
|---|---|---|---|---|
| TC-01 | Parser | Valid `LOGIN_FAILED` line | Structured event with expected fields | Automated test |
| TC-02 | Parser | Arbitrary text | Parser returns `None`; API returns HTTP 400 | Automated test |
| TC-03 | Parser | Invalid timestamp, IP, event type, or trailing content | Parser rejects line | Automated tests |
| TC-04 | Brute force | 3 failures for same user/IP within 60 seconds | `BRUTE_FORCE` alert | Automated test |
| TC-05 | Duplicate suppression | Additional matching failure during cooldown | No duplicate alert for same rule/user/IP | Automated test |
| TC-06 | Password spraying | At least 3 distinct usernames from one IP in 60 seconds | `PASSWORD_SPRAYING` alert | Automated test |
| TC-07 | Suspicious success | 3 failures then success for same user/IP | `SUSPICIOUS_SUCCESS`, `HIGH` | Automated test |
| TC-08 | Window expiry | Old failures fall outside the time window | Expired events do not contribute to threshold | Automated test |
| TC-09 | API history | Request `GET /api/alerts` after an alert | Alert appears in JSON history | API integration test |
| TC-10 | CSV | Request `GET /api/export/csv` | CSV with semicolon delimiter and one UTF-8 BOM | API integration test |
| TC-11 | WebSocket | Connect client and submit a triggering event | Client receives the new alert | API integration test; browser check still recommended |
| TC-12 | Dashboard | Open frontend through Compose and submit events | Table updates, filters/search work | Manual target-PC verification required |
| TC-13 | Docker | Start services from a clean checkout | Backend and frontend stay running | Manual target-PC verification required |
| TC-14 | Restart | Generate alerts and restart backend | Persisted alerts remain; in-memory correlation resets | Manual check recommended |
