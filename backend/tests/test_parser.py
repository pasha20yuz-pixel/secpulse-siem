from datetime import datetime

from app.parser import parse_log_line


def test_parse_valid_failed_login():
    event = parse_log_line(
        "[2026-10-12 12:00:00] LOGIN_FAILED user=admin ip=192.168.1.50"
    )
    assert event is not None
    assert event.event_type == "LOGIN_FAILED"
    assert event.username == "admin"
    assert event.ip_address == "192.168.1.50"
    assert event.timestamp == datetime(2026, 10, 12, 12, 0, 0)


def test_parse_valid_successful_login():
    event = parse_log_line(
        "[2026-10-12 12:00:01] LOGIN_SUCCESS user=pavel ip=10.0.0.2"
    )
    assert event is not None
    assert event.event_type == "LOGIN_SUCCESS"


def test_parse_rejects_malformed_line():
    assert parse_log_line("not a log line") is None


def test_parse_rejects_invalid_timestamp():
    assert parse_log_line(
        "[not-a-timestamp] LOGIN_FAILED user=admin ip=192.168.1.50"
    ) is None


def test_parse_rejects_invalid_ip_address():
    assert parse_log_line(
        "[2026-10-12 12:00:00] LOGIN_FAILED user=admin ip=999.999.999.999"
    ) is None


def test_parse_rejects_unsupported_event_type():
    assert parse_log_line(
        "[2026-10-12 12:00:00] DELETE_USER user=admin ip=192.168.1.50"
    ) is None


def test_parse_rejects_trailing_garbage():
    assert parse_log_line(
        "[2026-10-12 12:00:00] LOGIN_FAILED user=admin ip=192.168.1.50 extra"
    ) is None
