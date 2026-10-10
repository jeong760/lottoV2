# utils/audit_security.py
import sys
import os
import hashlib
import hmac
import json
import datetime
import logging
import copy
import tempfile
import threading
from typing import Dict, List, Any, Union, Optional

# Ensure project root is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir) if "utils" in current_dir else current_dir
if project_root not in sys.path:
    sys.path.insert(0, project_root)

_log = logging.getLogger("AuditTrailSecurity")
_LEGACY_SECRET_KEY = b"LottoV2_Audit_Security_Secret_Key_2026"


def _is_truthy_env(name: str) -> bool:
    return str(os.getenv(name, "") or "").strip().lower() in {"1", "true", "yes", "on"}


def _is_production_environment() -> bool:
    env_markers = ("LOTTO_ENV", "APP_ENV", "ENV", "PYTHON_ENV")
    for marker in env_markers:
        if str(os.getenv(marker, "") or "").strip().lower() in {"prod", "production"}:
            return True
    return _is_truthy_env("LOTTO_PRODUCTION")


def _load_audit_secret_key() -> bytes:
    """
    Loads the audit-signing key from environment or a local secret file.
    Priority:
      1) LOTTO_AUDIT_SECRET_KEY environment variable
      2) project-root db/.lotto_audit_secret (auto-generated if missing)
    """
    env_value = str(os.getenv("LOTTO_AUDIT_SECRET_KEY", "") or "").strip()
    if env_value:
        return env_value.encode("utf-8")

    secret_dir = os.path.join(project_root, "db")
    secret_path = os.path.join(secret_dir, ".lotto_audit_secret")

    try:
        if os.path.exists(secret_path):
            with open(secret_path, "rb") as f:
                data = f.read()
                if data:
                    return data
    except Exception as e:
        _log.warning("Failed to read persisted audit secret. detail=%s", e, exc_info=True)

    try:
        os.makedirs(secret_dir, exist_ok=True)
        generated = os.urandom(32)
        temporary_path = None
        try:
            with tempfile.NamedTemporaryFile(dir=secret_dir, delete=False) as f:
                temporary_path = f.name
                f.write(generated)
                f.flush()
                os.fsync(f.fileno())
            os.chmod(temporary_path, 0o600)
            try:
                os.link(temporary_path, secret_path)
            except FileExistsError:
                with open(secret_path, "rb") as f:
                    return f.read()
        finally:
            if temporary_path and os.path.exists(temporary_path):
                os.unlink(temporary_path)
        message = (
            "Generated a new local audit secret file. Set LOTTO_AUDIT_SECRET_KEY in production environments."
        )
        if _is_production_environment():
            _log.warning(message)
        else:
            _log.info(message)
        return generated
    except Exception as e:
        _log.warning(
            "Failed to persist audit secret; using ephemeral in-memory key. detail=%s",
            e,
            exc_info=True,
        )
        return os.urandom(32)


class AuditTrailSecurity:
    """
    Audit log and digital signature manager to ensure tamper-proof integrity 
    of generated lotto number sets, multi-algorithm ensemble contributions, and draw records.
    """
    
    # Internal secret key cache loaded from environment / managed secret storage.
    _SECRET_KEY = None
    _SECRET_KEY_LOCK = threading.Lock()

    @classmethod
    def _get_secret_key(cls) -> bytes:
        if isinstance(cls._SECRET_KEY, (bytes, bytearray)) and len(cls._SECRET_KEY) > 0:
            return bytes(cls._SECRET_KEY)
        with cls._SECRET_KEY_LOCK:
            if not isinstance(cls._SECRET_KEY, (bytes, bytearray)) or not cls._SECRET_KEY:
                cls._SECRET_KEY = _load_audit_secret_key()
            return bytes(cls._SECRET_KEY)

    @staticmethod
    def _json_default_converter(o: Any) -> Any:
        """Custom JSON serializer to convert non-standard objects safely."""
        if isinstance(o, (datetime.date, datetime.datetime)):
            return o.isoformat()
        if isinstance(o, set):
            return sorted(list(o))
        if hasattr(o, "tolist"):
            return o.tolist()
        return str(o)

    @classmethod
    def generate_hash(cls, data_dict: dict[str, Any], use_hmac: bool = True) -> str:
        """
        Converts given data into a deterministic JSON string format 
        and creates a SHA-256 / HMAC-SHA256 signature that changes completely if modified.
        """
        try:
            data_string = json.dumps(
                data_dict, 
                sort_keys=True, 
                ensure_ascii=False, 
                default=cls._json_default_converter
            )
            
            data_bytes = data_string.encode('utf-8')
            
            if use_hmac:
                signature = hmac.new(cls._get_secret_key(), data_bytes, hashlib.sha256).hexdigest()
            else:
                signature = hashlib.sha256(data_bytes).hexdigest()
                
            return signature
        except Exception as e:
            _log.error(f"Failed to generate cryptographic hash: {e}", exc_info=True)
            return ""

    @classmethod
    def create_signed_record(
        cls, 
        numbers: list[int] | tuple, 
        metadata: dict[str, Any] | None = None,
        ensemble_contributions: list[dict[str, Any]] | None = None
    ) -> dict[str, Any]:
        """
        Bundles generated lotto number sets with metadata and multi-algorithm ensemble 
        contributions to issue a secure record certificate containing a tamper-proof digital signature.
        """
        if metadata is None:
            metadata = {}

        clean_numbers = sorted([int(n) for n in numbers if n is not None and str(n).isdigit() and 1 <= int(n) <= 45])

        record = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "numbers": clean_numbers,
            "metadata": dict(metadata),
            "ensemble_contributions": ensemble_contributions if ensemble_contributions else []
        }
        
        signature = cls.generate_hash(record)
        record["signature"] = signature
        
        _log.debug(f"Created signed audit record with ensemble synergy for numbers: {clean_numbers}")
        return record

    @classmethod
    def verify_record(cls, record: dict[str, Any]) -> bool:
        """
        Strictly verifies via signature whether recorded data has been corrupted 
        or maliciously manipulated during database or file loading.
        """
        try:
            if not isinstance(record, dict) or "signature" not in record:
                _log.warning("Verification failed: Record is not a valid dictionary or missing signature.")
                return False

            record_copy = copy.deepcopy(record)
            original_signature = record_copy.pop("signature", None)
            
            if not original_signature:
                return False
                
            data_string = json.dumps(
                record_copy,
                sort_keys=True,
                ensure_ascii=False,
                default=cls._json_default_converter,
            ).encode("utf-8")
            keys = [cls._get_secret_key(), _LEGACY_SECRET_KEY]
            is_authentic = any(
                hmac.compare_digest(
                    str(original_signature),
                    hmac.new(key, data_string, hashlib.sha256).hexdigest(),
                )
                for key in keys
            )
            if not is_authentic:
                _log.warning("Tamper detection alert: Record signature mismatch detected!")
                
            return is_authentic
        except Exception as e:
            _log.error(f"Error during record verification: {e}", exc_info=True)
            return False