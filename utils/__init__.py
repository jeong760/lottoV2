# utils/__init__.py
import logging
import importlib
import os
import sys

# Ensure project root is in python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

# Note: Logging setup is centralized in launcher.py to prevent redundant or misplaced log directory creation.
_log = logging.getLogger("UtilsModule")

_UTILS_EXPORTS = {
    "setup_logger": ("utils.logger", "setup_logger"),
    "setup_logging_func": ("utils.logger", "setup_logging"),
    "AuditTrailSecurity": ("utils.audit_security", "AuditTrailSecurity"),
    "DBSync": ("utils.db_sync", "DBSync"),
    "ExcelImporter": ("utils.excel_importer", "ExcelImporter"),
}
_UTILS_CACHE = {}


def __getattr__(name):
    if name not in _UTILS_EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    if name in _UTILS_CACHE:
        return _UTILS_CACHE[name]

    module_name, attr_name = _UTILS_EXPORTS[name]
    try:
        module = importlib.import_module(module_name)
        value = getattr(module, attr_name)
    except Exception as e:
        _log.warning(f"[UtilsModule] Could not import {name}: {e}")
        value = None

    _UTILS_CACHE[name] = value
    return value

_log.info("[UtilsModule] Utils package initialization completed (lazy export mode).")

__all__ = [
    "setup_logger",
    "setup_logging_func",
    "AuditTrailSecurity",
    "DBSync",
    "ExcelImporter",
]