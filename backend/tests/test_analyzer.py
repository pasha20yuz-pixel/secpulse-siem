from datetime import datetime, timedelta

from app.analyzer import SecurityAnalyzer
from app.parser import SecurityEvent


def event(event_type, username, ip, seconds=0):
    return SecurityEvent(
        timestamp=datetime(2026, 10, 12, 12, 0, 0) + timedelta(seconds=seconds),
        event_type=event_type,
        username=username,
        ip_address=ip,
    )


def test_brute_force_alert_after_threshold():
    analyzer = SecurityAnalyzer(threshold=3, window_seconds=60)
    assert analyzer.process_event(event("LOGIN_FAILED", "admin", "192.0.2.10", 0)) == []
    assert analyzer.process_event(event("LOGIN_FAILED", "admin", "192.0.2.10", 1)) == []
    alerts = analyzer.process_event(event("LOGIN_FAILED", "admin", "192.0.2.10", 2))
    assert len(alerts) == 1
    assert alerts[0].alert_type == "BRUTE_FORCE"
    assert alerts[0].failed_attempts == 3


def test_repeated_brute_force_alert_is_suppressed_during_cooldown():
    analyzer = SecurityAnalyzer(threshold=3, window_seconds=60, alert_cooldown_seconds=60)
    for second in range(3):
        alerts = analyzer.process_event(event("LOGIN_FAILED", "admin", "192.0.2.20", second))
    assert any(alert.alert_type == "BRUTE_FORCE" for alert in alerts)
    alerts = analyzer.process_event(event("LOGIN_FAILED", "admin", "192.0.2.20", 3))
    assert not any(alert.alert_type == "BRUTE_FORCE" for alert in alerts)


def test_password_spraying_alerts_for_multiple_users_from_same_ip():
    analyzer = SecurityAnalyzer(threshold=3, window_seconds=60)
    analyzer.process_event(event("LOGIN_FAILED", "admin", "192.0.2.11", 0))
    analyzer.process_event(event("LOGIN_FAILED", "root", "192.0.2.11", 1))
    alerts = analyzer.process_event(event("LOGIN_FAILED", "guest", "192.0.2.11", 2))
    assert any(alert.alert_type == "PASSWORD_SPRAYING" for alert in alerts)
    next_alerts = analyzer.process_event(event("LOGIN_FAILED", "service", "192.0.2.11", 3))
    assert not any(alert.alert_type == "PASSWORD_SPRAYING" for alert in next_alerts)


def test_success_after_repeated_failures_is_flagged():
    analyzer = SecurityAnalyzer(threshold=3, window_seconds=60)
    for second in range(3):
        analyzer.process_event(event("LOGIN_FAILED", "admin", "192.0.2.12", second))
    alerts = analyzer.process_event(event("LOGIN_SUCCESS", "admin", "192.0.2.12", 4))
    assert any(alert.alert_type == "SUSPICIOUS_SUCCESS" for alert in alerts)
    assert next(a for a in alerts if a.alert_type == "SUSPICIOUS_SUCCESS").severity == "HIGH"


def test_old_failures_expire_outside_window():
    analyzer = SecurityAnalyzer(threshold=3, window_seconds=60)
    analyzer.process_event(event("LOGIN_FAILED", "admin", "192.0.2.13", 0))
    analyzer.process_event(event("LOGIN_FAILED", "admin", "192.0.2.13", 1))
    alerts = analyzer.process_event(event("LOGIN_FAILED", "admin", "192.0.2.13", 61))
    assert not any(alert.alert_type == "BRUTE_FORCE" for alert in alerts)
