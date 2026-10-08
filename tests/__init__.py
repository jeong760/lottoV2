# tests/__init__.py
"""
Unit tests and integration test suites for the Lotto 6/45 Analysis System.
"""
import logging
import os
import sys

# Ensure project root is in sys.path and initialize centralized logging for tests
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir) if "tests" in current_dir else current_dir
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from utils.logger import setup_logging
    setup_logging(project_root)
    _log = logging.getLogger("TestsPackage")
    _log.debug("Tests package logging initialized successfully.")
except ImportError:
    pass