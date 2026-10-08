# core/algorithms/__init__.py
import importlib
import logging
import sys
import os
from typing import Callable, List

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir)) if "algorithms" in current_dir else current_dir
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.logger import setup_logging
setup_logging(project_root)

_log = logging.getLogger("AlgorithmsPackage")

from .base import FUNCTION_ALGORITHM_REGISTRY, BaseAlgorithm, HistoricalContext, AlgorithmOutcome

_REGISTER_GROUP_CALLBACKS: List[Callable] = []
LOADED_ALGORITHM_GROUP_MODULES: List[str] = []


def _try_import_group(module_name: str, callback_names: List[str]):
    try:
        module = importlib.import_module(f"core.algorithms.{module_name}")
        LOADED_ALGORITHM_GROUP_MODULES.append(module_name)
    except Exception as e:
        _log.warning(f"Failed to import algorithm group module '{module_name}': {e}")
        return

    for callback_name in callback_names:
        callback = getattr(module, callback_name, None)
        if callable(callback):
            _REGISTER_GROUP_CALLBACKS.append(callback)


_try_import_group("group_statistics", ["register_group_statistics"])
_try_import_group("group_frequency", ["register_group_frequency"])
_try_import_group("group_ml_ai", ["register_group_ml"])
_try_import_group("group_pattern", ["register_group_pattern"])
_try_import_group("group_advanced", ["register_group_advanced"])


class MasterAlgorithmRegistry:
    """Central registry holding all algorithm instances and function mappings."""

    def __init__(self):
        self.algorithms = {}

    def register(self, algorithm_instance):
        if hasattr(algorithm_instance, "name"):
            self.algorithms[algorithm_instance.name] = algorithm_instance

    def initialize_all(self):
        _log.info("Initializing and registering all algorithm groups...")
        for register_callback in _REGISTER_GROUP_CALLBACKS:
            try:
                register_callback(self)
            except Exception as e:
                _log.warning(
                    f"Algorithm group callback '{getattr(register_callback, '__name__', 'unknown')}' failed: {e}",
                    exc_info=True,
                )

        _log.info(
            "Successfully registered %s class-based algorithms and %s function-based algorithms (loaded groups: %s).",
            len(self.algorithms),
            len(FUNCTION_ALGORITHM_REGISTRY),
            ", ".join(LOADED_ALGORITHM_GROUP_MODULES) if LOADED_ALGORITHM_GROUP_MODULES else "none",
        )


__all__ = [
    "MasterAlgorithmRegistry",
    "FUNCTION_ALGORITHM_REGISTRY",
    "BaseAlgorithm",
    "HistoricalContext",
    "AlgorithmOutcome",
    "LOADED_ALGORITHM_GROUP_MODULES",
]
