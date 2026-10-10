# ui/__init__.py
import logging
import importlib
import os
import sys

# Ensure project root is in python path and initialize centralized logging
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from utils.logger import setup_logging
setup_logging(project_root)

_log = logging.getLogger("UIModule")

_UI_EXPORTS = {
    "MainWindow": ("ui.main_window", "MainWindow"),
    "SimulationController": ("ui.controllers.simulation_controller", "SimulationController"),
    "DataSyncController": ("ui.controllers.data_sync_controller", "DataSyncController"),
    "StatisticsWidgetConnector": ("ui.controllers.data_sync_controller", "StatisticsWidgetConnector"),
}
_UI_CACHE = {}


def __getattr__(name):
    if name not in _UI_EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    if name in _UI_CACHE:
        return _UI_CACHE[name]

    module_name, attr_name = _UI_EXPORTS[name]
    try:
        module = importlib.import_module(module_name)
        value = getattr(module, attr_name)
    except Exception as e:
        _log.warning(f"[UIModule] Could not import '{name}': {e}")
        value = None

    _UI_CACHE[name] = value
    return value

_log.info("[UIModule] UI package initialization completed (lazy export mode).")

__all__ = [
    "MainWindow",
    "SimulationController",
    "DataSyncController",
    "StatisticsWidgetConnector",
]