# workers/__init__.py
import logging
import os
import sys
import importlib

# Ensure project root is in python path and initialize centralized logging
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from utils.logger import setup_logging
setup_logging(project_root)

_log = logging.getLogger("WorkersModule")

LottoWorker = None
AITrainWorker = None

def _lazy_import_worker(module_name: str, class_name: str):
    try:
        module = importlib.import_module(f"workers.{module_name}")
    except Exception:
        module = importlib.import_module(f".{module_name}", package=__name__)
    return getattr(module, class_name)


def __getattr__(name):
    global LottoWorker, AITrainWorker

    if name == "LottoWorker":
        if LottoWorker is None:
            try:
                LottoWorker = _lazy_import_worker("lotto_worker", "LottoWorker")
            except Exception as e:
                _log.warning(f"[WorkersModule] Could not import 'LottoWorker': {e}")
                LottoWorker = None
        return LottoWorker

    if name == "AITrainWorker":
        if AITrainWorker is None:
            try:
                AITrainWorker = _lazy_import_worker("ai_train_worker", "AITrainWorker")
            except Exception as e:
                _log.warning(f"[WorkersModule] Could not import 'AITrainWorker': {e}")
                AITrainWorker = None
        return AITrainWorker

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


_log.info("[WorkersModule] Workers package initialization completed (lazy worker import mode).")

__all__ = [
    "LottoWorker",
    "AITrainWorker",
]