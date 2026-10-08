# -*- coding: utf-8 -*-
# workers/__init__.py
import logging
import os
import sys

# Ensure project root is in python path and initialize centralized logging
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from utils.logger import setup_logging
setup_logging(project_root)

_log = logging.getLogger("WorkersModule")

LottoWorker = None
AITrainWorker = None

# Safe import of worker classes
try:
    from workers.lotto_worker import LottoWorker
except ImportError:
    try:
        from .lotto_worker import LottoWorker
    except ImportError as e:
        _log.warning(f"[WorkersModule] Could not import 'LottoWorker': {e}")

try:
    from workers.ai_train_worker import AITrainWorker
except ImportError:
    try:
        from .ai_train_worker import AITrainWorker
    except ImportError as e:
        _log.warning(f"[WorkersModule] Could not import 'AITrainWorker': {e}")

_log.info("[WorkersModule] Workers package initialization completed.")

__all__ = [
    "LottoWorker",
    "AITrainWorker",
]