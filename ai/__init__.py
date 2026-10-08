# ai/__init__.py
import logging

_log = logging.getLogger("AIModule")

LottoAILearningModel = None

# Safe import of LottoAILearningModel class from ai package
try:
    from ai.ai_learning_model import LottoAILearningModel
except ImportError:
    try:
        from .ai_learning_model import LottoAILearningModel
    except ImportError as e:
        _log.warning(f"[AIModule] Could not import 'LottoAILearningModel': {e}")

_log.info("[AIModule] AI package initialization completed.")

__all__ = [
    "LottoAILearningModel",
]