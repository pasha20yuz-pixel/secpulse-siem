# Detection rules

These are educational heuristics implemented in `backend/app/analyzer.py`; they are not validated production detection policies.

## Input format

```text
[YYYY-MM-DD HH:MM:SS] LOGIN_FAILED user=<username> ip=<address>
[YYYY-MM-DD HH:MM:SS] LOGIN_SUCCESS user=<username> ip=<address>
```

The parser accepts only `LOGIN_FAILED` and `LOGIN_SUCCESS`, requires the timestamp to match `YYYY-MM-DD HH:MM:SS`, validates IPv4/IPv6 syntax, and rejects trailing content.

## Rules

| Rule | Condition | Alert type | Severity |
|---|---|---|---|
| Repeated failures for one account from one IP | At least 3 failures for the same username and IP in the last 60 seconds | `BRUTE_FORCE` | Count-based |
| Failures across multiple accounts from one IP | At least 3 distinct usernames among failures from the same IP in the last 60 seconds | `PASSWORD_SPRAYING` | Count-based |
| Successful login after repeated failures | A successful event matches a username and IP with at least 3 recent failures | `SUSPICIOUS_SUCCESS` | `HIGH` |

Default threshold: 3; correlation window: 60 seconds. Severity mapping for count-based rules: 3–5 is `LOW`, 6–9 is `MEDIUM`, and 10 or more is `HIGH`.

## Duplicate-alert cooldown

The analyzer suppresses another alert with the same combination of alert type, username, and IP during a 60-second cooldown. This reduces repeated notifications for a continuing pattern; it does not merge, resolve, or persist incidents as long-lived cases.

## Caveats

- Detection history and cooldown state are in process memory and reset after backend restart.
- For password spraying, `failed_attempts` reports the count of matching failed events, while the detection condition uses the number of distinct usernames.
- The implementation does not normalize usernames, maintain trusted-source lists, or robustly handle clock skew.
- Rules may produce false positives and have not been validated against production telemetry.
