# -*- coding: utf-8 -*-
# utils/audit_security.py
sys = __import__('sys')
os = __import__('os')
import hashlib
import hmac
import json
import datetime
import logging
import copy
from typing import Dict, List, Any, Union, Optional

# Ensure project root is in sys.path and initialize centralized logging
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir) if "utils" in current_dir else current_dir
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.logger import setup_logging
setup_logging(project_root)

_log = logging.getLogger("AuditTrailSecurity")


class AuditTrailSecurity:
    """
    Audit log and digital signature manager to ensure tamper-proof integrity 
    of generated lotto number sets, multi-algorithm ensemble contributions, and draw records.
    """
    
    # Internal secret key used for HMAC signature hashing to prevent signature forge
    _SECRET_KEY = b"LottoV2_Audit_Security_Secret_Key_2026"

    @staticmethod
    def _json_default_converter(o: Any) -> Any:
        """Custom JSON serializer to convert non-standard objects safely."""
        if isinstance(o, (datetime.date, datetime.datetime)):
            return o.isoformat()
        if isinstance(o, set):
            return sorted(list(o))
        if hasattr(o, "tolist"):
            return o.tolist()
        # Handle numpy scalars safely if numpy is available
        try:
            import numpy as np
            if isinstance(o, np.integer):
                return int(o)
            if isinstance(o, np.floating):
                return float(o)
            if isinstance(o, np.ndarray):
                return o.tolist()
        except ImportError:
            pass
        return str(o)

    @classmethod
    def generate_hash(cls, data_dict: Dict[str, Any], use_hmac: bool = True) -> str:
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
                signature = hmac.new(cls._SECRET_KEY, data_bytes, hashlib.sha256).hexdigest()
            else:
                signature = hashlib.sha256(data_bytes).hexdigest()
                
            return signature
        except Exception as e:
            _log.error(f"Failed to generate cryptographic hash: {e}", exc_info=True)
            return ""

    @classmethod
    def create_signed_record(
        cls, 
        numbers: Union[List[int], tuple], 
        metadata: Optional[Dict[str, Any]] = None,
        ensemble_contributions: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
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
    def verify_record(cls, record: Dict[str, Any]) -> bool:
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
                
            recalculated_signature = cls.generate_hash(record_copy)
            
            is_authentic = hmac.compare_digest(str(original_signature), str(recalculated_signature))
            if not is_authentic:
                _log.warning("Tamper detection alert: Record signature mismatch detected!")
                
            return is_authentic
        except Exception as e:
            _log.error(f"Error during record verification: {e}", exc_info=True)
            return False


# =====================================================================
# Test execution block (Security system trial run)
# =====================================================================
if __name__ == "__main__":
    setup_logging(project_root)
    _log.info("Starting security and audit trail module tests...")
    print("Starting security and audit trail module tests...\n")
    
    sample_numbers = [3, 12, 24, 31, 38, 45]
    sample_metadata = {"algorithm": "Ensemble-Meta-001", "confidence": 0.95}
    sample_ensemble = [
        {"algorithm_name": "ALG-001 | Stat_TimeSeries", "weight": 0.4},
        {"algorithm_name": "ALG-150 | Advanced_Quantum_Hybrid", "weight": 0.6}
    ]
    
    secure_record = AuditTrailSecurity.create_signed_record(
        sample_numbers, sample_metadata, sample_ensemble
    )
    print("Generated secure record (JSON):")
    print(json.dumps(secure_record, indent=4, ensure_ascii=False))
    print("-" * 60)
    
    is_valid = AuditTrailSecurity.verify_record(secure_record)
    print(f"[Normal Verification] Is this record safe? -> {is_valid} (Should be True)")
    
    tampered_record = copy.deepcopy(secure_record)
    tampered_record["numbers"][0] = 4 
    
    is_tampered_valid = AuditTrailSecurity.verify_record(tampered_record)
    print(f"[Tamper Detection Test] Is the tampered record safe? -> {is_tampered_valid} (Should block as False!)")