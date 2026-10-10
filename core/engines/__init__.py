# core/engines/__init__.py
import sys
import os
import logging

# Ensure project root is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir)) if "engines" in current_dir else current_dir
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Note: Logging setup is centralized in launcher.py to prevent redundant or misplaced log directory creation.
_log = logging.getLogger("CoreModule")

__all__ = [
    "AIEngine",
    "LottoEngine",
    "StatisticsEngine",
    "MarkovTransitionEngine",
    "MonteCarloValidator",
    "MLEngineRunner",  # Retained for compatibility, mapped to AIEngine
]

def __getattr__(name):
    """Lazy load engine classes on demand to prevent circular imports."""
    if name == "AIEngine":
        try:
            # Note: AIEngine is implemented in core/ai_engine.py or core/engines/ai_engine.py
            try:
                from core.engines.ai_engine import AIEngine
            except ImportError:
                from core.ai_engine import AIEngine
            return AIEngine
        except ImportError as e:
            _log.error(f"Failed to load AIEngine: {e}")
            return None

    elif name == "LottoEngine":
        try:
            from core.engines.lotto_engine import LottoEngine
            return LottoEngine
        except ImportError as e:
            _log.error(f"Failed to load LottoEngine: {e}")
            return None
            
    elif name == "StatisticsEngine":
        try:
            from core.engines.statistics_engine import StatisticsEngine
            return StatisticsEngine
        except ImportError as e:
            _log.error(f"Failed to load StatisticsEngine: {e}")
            return None

    elif name == "MarkovTransitionEngine":
        try:
            from core.engines.markov_transition_engine import MarkovTransitionEngine
            return MarkovTransitionEngine
        except ImportError as e:
            _log.error(f"Failed to load MarkovTransitionEngine: {e}")
            return None

    elif name == "MonteCarloValidator":
        try:
            from core.engines.monte_carlo_validator import MonteCarloValidator
            return MonteCarloValidator
        except ImportError as e:
            _log.error(f"Failed to load MonteCarloValidator: {e}")
            return None

    elif name == "MLEngineRunner":
        # Since MLEngineRunner was integrated into ai_engine, map it safely to AIEngine
        try:
            try:
                from core.engines.ai_engine import AIEngine as MLEngineRunner
            except ImportError:
                from core.ai_engine import AIEngine as MLEngineRunner
            return MLEngineRunner
        except ImportError as e:
            _log.warning(f"MLEngineRunner fallback mapping failed: {e}")
            return None

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")