# core/algorithms/__init__.py
import logging
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir)) if "algorithms" in current_dir else current_dir
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.logger import setup_logging
setup_logging(project_root)

_log = logging.getLogger("AlgorithmsPackage")

# Import all group registration functions
from .group_statistics import register_group_statistics
from .group_frequency import register_group_frequency
from .group_ml_ai import register_group_ml, register_group_ai
from .group_pattern import register_group_pattern
from .group_advanced import register_group_advanced
from .base import FUNCTION_ALGORITHM_REGISTRY, BaseAlgorithm, HistoricalContext, AlgorithmOutcome

class MasterAlgorithmRegistry:
    """Central registry holding all algorithm instances and function mappings."""
    def __init__(self):
        self.algorithms = {}

    def register(self, algorithm_instance):
        if hasattr(algorithm_instance, "name"):
            self.algorithms[algorithm_instance.name] = algorithm_instance

    def initialize_all(self):
        _log.info("Initializing and registering all algorithm groups...")
        try:
            register_group_statistics(self)
            register_group_frequency(self)
            register_group_ml(self)
            register_group_pattern(self)
            register_group_advanced(self)
            _log.info(f"Successfully registered {len(self.algorithms)} class-based algorithms and {len(FUNCTION_ALGORITHM_REGISTRY)} function-based algorithms.")
        except Exception as e:
            _log.error(f"Error during algorithm group registration: {e}", exc_info=True)

__all__ = [
    "MasterAlgorithmRegistry",
    "FUNCTION_ALGORITHM_REGISTRY",
    "BaseAlgorithm",
    "HistoricalContext",
    "AlgorithmOutcome"
]