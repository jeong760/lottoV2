import concurrent.futures
import hashlib
import hmac
import json

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


def test_signed_records_filter_numbers_to_lotto_range():
    record = AuditTrailSecurity.create_signed_record([0, 1, 45, 99])

    assert record["numbers"] == [1, 45]
