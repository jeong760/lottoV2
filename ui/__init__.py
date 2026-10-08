# -*- coding: utf-8 -*-
# ui/__init__.py
import logging
import os
import sys

# Ensure project root is in python path and initialize centralized logging
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from utils.logger import setup_logging
setup_logging(project_root)

_log = logging.getLogger("UIModule")

MainWindow = None
SimulationController = None
DataSyncController = None

# Safe import of MainWindow from ui.main_window module
try:
    from ui.main_window import MainWindow
except ImportError:
    try:
        from .main_window import MainWindow
    except ImportError as e:
        _log.warning(f"[UIModule] Could not import 'MainWindow': {e}")

# Safe import of modular controllers
try:
    from ui.controllers.simulation_controller import SimulationController
except ImportError:
    try:
        from .controllers.simulation_controller import SimulationController
    except ImportError as e:
        _log.warning(f"[UIModule] Could not import 'SimulationController': {e}")

try:
    from ui.controllers.data_sync_controller import DataSyncController, StatisticsWidgetConnector
except ImportError:
    try:
        from .controllers.data_sync_controller import DataSyncController, StatisticsWidgetConnector
    except ImportError as e:
        _log.warning(f"[UIModule] Could not import 'DataSyncController': {e}")

_log.info("[UIModule] UI package initialization completed.")

__all__ = [
    "MainWindow",
    "SimulationController",
    "DataSyncController",
    "StatisticsWidgetConnector",
]