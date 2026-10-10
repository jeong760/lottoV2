# core/__init__.py
import sys
import os
import types
import logging

# Ensure project root is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir) if "core" in current_dir else current_dir
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Note: Logging setup is centralized in launcher.py to prevent redundant or misplaced log directory creation.
_log = logging.getLogger("CoreModule")

# Force inject sys.modules alias for backward compatibility with 'core.statistics_engine'
try:
    from core.engines.statistics_engine import StatisticsEngine
    stat_mod = types.ModuleType("core.statistics_engine")
    stat_mod.StatisticsEngine = StatisticsEngine
    sys.modules["core.statistics_engine"] = stat_mod
except Exception as e:
    _log.warning(f"[CoreModule] Failed to inject statistics_engine alias: {e}")

__all__ = [
    "AlgorithmHub",
    "AIEngine",
    "LottoEvaluator",
    "Security",
    "StatisticsController",
    "StatisticsEngine",
]

def __getattr__(name):
    """Lazy load core modules on demand to prevent circular imports."""
    if name == "AlgorithmHub":
        try:
            from core.algorithm_hub import AlgorithmHub
            return AlgorithmHub
        except ImportError:
            try:
                from .algorithm_hub import AlgorithmHub
                return AlgorithmHub
            except ImportError as e:
                _log.warning(f"[CoreModule] Could not import AlgorithmHub: {e}")
                return None
                
    elif name == "AIEngine":
        try:
            from core.engines.ai_engine import AIEngine
            return AIEngine
        except ImportError as e:
            _log.warning(f"[CoreModule] Could not import AIEngine: {e}")
            return None
                
    elif name == "LottoEvaluator":
        try:
            from core.lotto_evaluator import LottoEvaluator
            return LottoEvaluator
        except ImportError:
            try:
                from .lotto_evaluator import LottoEvaluator
                return LottoEvaluator
            except ImportError as e:
                _log.warning(f"[CoreModule] Could not import LottoEvaluator: {e}")
                return None
                
    elif name == "Security":
        try:
            from core.security import Security
            return Security
        except ImportError:
            try:
                from .security import Security
                return Security
            except ImportError as e:
                _log.warning(f"[CoreModule] Could not import Security: {e}")
                return None
                
    elif name == "StatisticsController":
        try:
            from core.statistics_controller import StatisticsController
            return StatisticsController
        except ImportError:
            try:
                from .statistics_controller import StatisticsController
                return StatisticsController
            except ImportError as e:
                _log.warning(f"[CoreModule] Could not import StatisticsController: {e}")
                return None

    elif name == "StatisticsEngine":
        try:
            from core.engines.statistics_engine import StatisticsEngine
            return StatisticsEngine
        except ImportError as e:
            _log.warning(f"[CoreModule] Could not import StatisticsEngine: {e}")
            return None
                
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

_log.info("[CoreModule] Core package initialization completed safely.")