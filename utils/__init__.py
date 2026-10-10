# utils/__init__.py
import logging
import os
import sys

# Ensure project root is in python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

# Note: Logging setup is centralized in launcher.py to prevent redundant or misplaced log directory creation.
_log = logging.getLogger("UtilsModule")

setup_logger = None
setup_logging_func = None
AuditTrailSecurity = None
DBSync = None
ExcelImporter = None

# 1. Safe import of setup_logger, setup_logging, and AuditTrailSecurity
try:
    from utils.logger import setup_logger, setup_logging as setup_logging_func
except ImportError:
    try:
        from .logger import setup_logger, setup_logging as setup_logging_func
    except ImportError as e:
        _log.warning(f"[UtilsModule] Could not import logging setup functions: {e}")

try:
    from utils.audit_security import AuditTrailSecurity
except ImportError:
    try:
        from .audit_security import AuditTrailSecurity
    except ImportError as e:
        _log.warning(f"[UtilsModule] Could not import AuditTrailSecurity: {e}")

# 2. Safe import of DBSync (db_sync.py)
try:
    from utils.db_sync import DBSync
except ImportError:
    try:
        from .db_sync import DBSync
    except ImportError as e:
        _log.warning(f"[UtilsModule] Could not import DBSync: {e}")

# 3. Safe import of ExcelImporter (excel_importer.py)
try:
    from utils.excel_importer import ExcelImporter
except ImportError:
    try:
        from .excel_importer import ExcelImporter
    except ImportError as e:
        _log.warning(f"[UtilsModule] Could not import ExcelImporter: {e}")

_log.info("[UtilsModule] Utils package initialization completed.")

__all__ = [
    "setup_logger",
    "setup_logging_func",
    "AuditTrailSecurity",
    "DBSync",
    "ExcelImporter",
]