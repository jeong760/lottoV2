# data/repositories/__init__.py
import logging
import os
import sys

# Ensure project root is in sys.path and initialize centralized logging
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir)) if "repositories" in current_dir else current_dir
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.logger import setup_logging
setup_logging(project_root)

_log = logging.getLogger("RepositoriesModule")

LottoRepository = None
MLModelRepository = None

# 1. Safe import of LottoRepository
try:
    from data.repositories.lotto_repository import LottoRepository
except ImportError:
    try:
        from .lotto_repository import LottoRepository
    except ImportError as e:
        _log.warning(f"[RepositoriesModule] Could not import 'LottoRepository': {e}")

# 2. Safe import of MLModelRepository
try:
    from data.repositories.ml_model_repository import MLModelRepository
except ImportError:
    try:
        from .ml_model_repository import MLModelRepository
    except ImportError as e:
        _log.warning(f"[RepositoriesModule] Could not import 'MLModelRepository': {e}")

_log.info("[RepositoriesModule] Repositories package initialization completed.")

__all__ = [
    "LottoRepository",
    "MLModelRepository",
]