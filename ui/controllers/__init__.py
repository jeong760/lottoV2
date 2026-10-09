# ui/controllers/__init__.py
import logging
import os
import sys

# Ensure project root is in python path and initialize centralized logging
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.logger import setup_logging
setup_logging(project_root)

_log = logging.getLogger("ControllersModule")

SimulationController = None
DataSyncController = None
StatisticsWidgetConnector = None

# 1. Safe import of SimulationController
try:
    from ui.controllers.simulation_controller import SimulationController
except ImportError:
    try:
        from .simulation_controller import SimulationController
    except ImportError as e:
        _log.warning(f"[ControllersModule] Could not import 'SimulationController': {e}")

# 2. Safe import of DataSyncController and StatisticsWidgetConnector
try:
    from ui.controllers.data_sync_controller import DataSyncController, StatisticsWidgetConnector
except ImportError:
    try:
        from .data_sync_controller import DataSyncController, StatisticsWidgetConnector
    except ImportError as e:
        _log.warning(f"[ControllersModule] Could not import 'DataSyncController': {e}")

_log.info("[ControllersModule] Controllers package initialization completed safely.")

__all__ = [
    "SimulationController",
    "DataSyncController",
    "StatisticsWidgetConnector",
]