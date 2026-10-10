import concurrent.futures
import hashlib
import hmac
import json
import logging

from utils import audit_security
from utils.audit_security import AuditTrailSecurity


def test_verifies_records_signed_with_legacy_key(monkeypatch):
    record = {
        "timestamp": "2026-01-01 00:00:00",
        "numbers": [1, 2, 3, 4, 5, 6],
        "metadata": {},
        "ensemble_contributions": [],
    }
    payload = json.dumps(record, sort_keys=True, ensure_ascii=False).encode("utf-8")
    record["signature"] = hmac.new(
        audit_security._LEGACY_SECRET_KEY, payload, hashlib.sha256
    ).hexdigest()
    monkeypatch.setattr(AuditTrailSecurity, "_SECRET_KEY", b"new signing key")

    assert AuditTrailSecurity.verify_record(record)


def test_audit_secret_creation_is_atomic_for_concurrent_callers(tmp_path, monkeypatch):
    monkeypatch.delenv("LOTTO_AUDIT_SECRET_KEY", raising=False)
    monkeypatch.setattr(audit_security, "project_root", str(tmp_path))
    secret_path = tmp_path / "db" / ".lotto_audit_secret"

    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
        keys = list(executor.map(lambda _: audit_security._load_audit_secret_key(), range(24)))

    assert all(key == keys[0] for key in keys)
    assert secret_path.read_bytes() == keys[0]


def test_audit_secret_generation_logs_info_outside_production(tmp_path, monkeypatch, caplog):
    monkeypatch.delenv("LOTTO_AUDIT_SECRET_KEY", raising=False)
    monkeypatch.delenv("LOTTO_ENV", raising=False)
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("ENV", raising=False)
    monkeypatch.delenv("PYTHON_ENV", raising=False)
    monkeypatch.delenv("LOTTO_PRODUCTION", raising=False)
    monkeypatch.setattr(audit_security, "project_root", str(tmp_path))

    with caplog.at_level(logging.INFO, logger="AuditTrailSecurity"):
        audit_security._load_audit_secret_key()

    msg = "Generated a new local audit secret file. Set LOTTO_AUDIT_SECRET_KEY in production environments."
    records = [record for record in caplog.records if msg in record.getMessage()]
    assert records
    assert all(record.levelname == "INFO" for record in records)


def test_audit_secret_generation_logs_warning_in_production(tmp_path, monkeypatch, caplog):
    monkeypatch.delenv("LOTTO_AUDIT_SECRET_KEY", raising=False)
    monkeypatch.setenv("LOTTO_ENV", "production")
    monkeypatch.setattr(audit_security, "project_root", str(tmp_path))

    with caplog.at_level(logging.INFO, logger="AuditTrailSecurity"):
        audit_security._load_audit_secret_key()

    msg = "Generated a new local audit secret file. Set LOTTO_AUDIT_SECRET_KEY in production environments."
    records = [record for record in caplog.records if msg in record.getMessage()]
    assert records
    assert all(record.levelname == "WARNING" for record in records)


def test_signed_records_filter_numbers_to_lotto_range():
    record = AuditTrailSecurity.create_signed_record([0, 1, 45, 99])

    assert record["numbers"] == [1, 45]
