# ui/controllers/__init__.py
import logging
import importlib
import os
import sys

# Ensure project root is in python path and initialize centralized logging
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.logger import setup_logging
setup_logging(project_root)

_log = logging.getLogger("ControllersModule")

_CONTROLLER_EXPORTS = {
    "SimulationController": ("ui.controllers.simulation_controller", "SimulationController"),
    "DataSyncController": ("ui.controllers.data_sync_controller", "DataSyncController"),
    "StatisticsWidgetConnector": ("ui.controllers.data_sync_controller", "StatisticsWidgetConnector"),
}
_CONTROLLER_CACHE = {}


def __getattr__(name):
    if name not in _CONTROLLER_EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    if name in _CONTROLLER_CACHE:
        return _CONTROLLER_CACHE[name]

    module_name, attr_name = _CONTROLLER_EXPORTS[name]
    try:
        module = importlib.import_module(module_name)
        value = getattr(module, attr_name)
    except Exception as e:
        _log.warning(f"[ControllersModule] Could not import '{name}': {e}")
        value = None

    _CONTROLLER_CACHE[name] = value
    return value

_log.info("[ControllersModule] Controllers package initialization completed safely (lazy export mode).")

__all__ = [
    "SimulationController",
    "DataSyncController",
    "StatisticsWidgetConnector",
]