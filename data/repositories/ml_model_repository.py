# -*- coding: utf-8 -*-
# data/repositories/ml_model_repository.py
import sqlite3
import os
import sys
import json
import logging
import threading
import traceback
from typing import Optional, Dict, Any, List

# Ensure project root is in sys.path and initialize centralized logging
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir)) if "repositories" in current_dir else current_dir
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.logger import setup_logging
setup_logging(project_root)
try:
    from utils.audit_security import AuditTrailSecurity
except ImportError:
    AuditTrailSecurity = None

_log = logging.getLogger("MLModelRepository")


class MLModelRepository:
    """
    Dedicated repository managing machine learning training states, serialized weight blobs,
    model checkpoints, and cryptographic audit signatures via db/mllearn.db with thread safety.
    """
    
    _lock = threading.Lock()
    
    @staticmethod
    def _get_db_path() -> str:
        try:
            current_script_dir = os.path.dirname(os.path.abspath(__file__))
            proj_root = os.path.dirname(os.path.dirname(current_script_dir))
            db_dir = os.path.join(proj_root, "db")
            if not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
            return os.path.join(db_dir, "mllearn.db")
        except Exception as e:
            _log.warning(f"Error resolving mllearn.db path: {e}")
            fallback_dir = os.path.join(project_root, "db")
            os.makedirs(fallback_dir, exist_ok=True)
            return os.path.join(fallback_dir, "mllearn.db")

    @classmethod
    def _init_db(cls):
        """Initializes the database schema for JSON states and weight blobs safely."""
        with cls._lock:
            conn = None
            try:
                db_path = cls._get_db_path()
                conn = sqlite3.connect(db_path, timeout=10.0)
                cursor = conn.cursor()
                cursor.execute("PRAGMA journal_mode=WAL;")
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS ml_model_states (
                        key TEXT PRIMARY KEY,
                        model_type TEXT,
                        state_data TEXT,
                        signature TEXT,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS ml_weights (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        trained_at TEXT,
                        lstm_status TEXT,
                        weights_blob BLOB,
                        trend_score REAL,
                        signature TEXT
                    )
                """)

                for table in ["ml_model_states", "ml_weights"]:
                    try:
                        cursor.execute(f"ALTER TABLE {table} ADD COLUMN signature TEXT;")
                    except sqlite3.OperationalError:
                        pass

                conn.commit()
            except Exception as e:
                _log.error(f"Failed to initialize mllearn.db schema: {e}", exc_info=True)
            finally:
                if conn:
                    try:
                        conn.close()
                    except Exception:
                        pass

    @staticmethod
    def _sanitize_dict_keys(data: Any) -> Any:
        """Safely converts tuple or non-string dictionary keys into string format for JSON serialization."""
        try:
            if isinstance(data, dict):
                new_dict = {}
                for k, v in data.items():
                    if isinstance(k, tuple):
                        new_key = f"{k[0]},{k[1]}"
                    else:
                        new_key = str(k)
                    new_dict[new_key] = MLModelRepository._sanitize_dict_keys(v)
                return new_dict
            elif isinstance(data, list):
                return [MLModelRepository._sanitize_dict_keys(item) for item in data]
            return data
        except Exception:
            return data

    @classmethod
    def save_model_state(cls, key: str, model_type: str, state_dict: Dict[str, Any]) -> bool:
        """Saves or updates a machine learning model state dictionary in SQLite DB safely without locking."""
        cls._init_db()
        with cls._lock:
            conn = None
            try:
                db_path = cls._get_db_path()
                conn = sqlite3.connect(db_path, timeout=10.0)
                cursor = conn.cursor()
                
                sanitized_state = cls._sanitize_dict_keys(state_dict)

                def default_converter(o):
                    try:
                        if hasattr(o, "tolist"):
                            return o.tolist()
                        return str(o)
                    except Exception:
                        return ""

                data_str = json.dumps(sanitized_state, ensure_ascii=False, default=default_converter)
                
                signature = ""
                if AuditTrailSecurity is not None:
                    try:
                        signed_record = AuditTrailSecurity.create_signed_record(
                            numbers=[],
                            metadata={"key": key, "model_type": model_type},
                            ensemble_contributions=[{"model_type": model_type, "key": key}]
                        )
                        signature = signed_record.get("signature", "")
                    except Exception:
                        pass

                cursor.execute("""
                    INSERT OR REPLACE INTO ml_model_states (key, model_type, state_data, signature, updated_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (key, model_type, data_str, signature))
                
                conn.commit()
                _log.info(f"Model state '{key}' ({model_type}) saved securely to mllearn.db.")
                return True
            except Exception as e:
                _log.error(f"[CRITICAL DEBUG] Failed to save model state '{key}': {e}\n{traceback.format_exc()}")
                return False
            finally:
                if conn:
                    try:
                        conn.close()
                    except Exception:
                        pass

    @classmethod
    def load_model_state(cls, key: str = "default") -> Optional[Dict[str, Any]]:
        cls._init_db()
        with cls._lock:
            conn = None
            try:
                db_path = cls._get_db_path()
                conn = sqlite3.connect(db_path, timeout=10.0)
                cursor = conn.cursor()
                cursor.execute("SELECT state_data FROM ml_model_states WHERE key = ?", (key,))
                row = cursor.fetchone()
                if row and row[0]:
                    return json.loads(row[0])
                return None
            except Exception as e:
                _log.error(f"Failed to retrieve model state '{key}': {e}", exc_info=True)
                return None
            finally:
                if conn:
                    try:
                        conn.close()
                    except Exception:
                        pass

    @classmethod
    def get_latest_weights_blob(cls) -> Optional[bytes]:
        cls._init_db()
        with cls._lock:
            conn = None
            try:
                db_path = cls._get_db_path()
                conn = sqlite3.connect(db_path, timeout=10.0)
                cursor = conn.cursor()
                cursor.execute("SELECT weights_blob FROM ml_weights ORDER BY id DESC LIMIT 1")
                row = cursor.fetchone()
                if row and row[0]:
                    return row[0]
                return None
            except Exception as e:
                _log.error(f"Failed to retrieve latest weights blob: {e}", exc_info=True)
                return None
            finally:
                if conn:
                    try:
                        conn.close()
                    except Exception:
                        pass

    @classmethod
    def get_all_model_keys(cls) -> List[Dict[str, str]]:
        cls._init_db()
        with cls._lock:
            conn = None
            try:
                db_path = cls._get_db_path()
                conn = sqlite3.connect(db_path, timeout=10.0)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT key, model_type, updated_at FROM ml_model_states ORDER BY updated_at DESC")
                return [dict(row) for row in cursor.fetchall()]
            except Exception as e:
                _log.error(f"Failed to fetch model keys: {e}", exc_info=True)
                return []
            finally:
                if conn:
                    try:
                        conn.close()
                    except Exception:
                        pass

    @classmethod
    def delete_model_state(cls, key: str) -> bool:
        cls._init_db()
        with cls._lock:
            conn = None
            try:
                db_path = cls._get_db_path()
                conn = sqlite3.connect(db_path, timeout=10.0)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM ml_model_states WHERE key = ?", (key,))
                conn.commit()
                return True
            except Exception as e:
                _log.error(f"Failed to delete model state '{key}': {e}", exc_info=True)
                return False
            finally:
                if conn:
                    try:
                        conn.close()
                    except Exception:
                        pass