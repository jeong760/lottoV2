# data/__init__.py
import logging
import os
import sys

# Ensure project root is in sys.path and initialize centralized logging
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir) if "data" in current_dir else current_dir
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.logger import setup_logging
setup_logging(project_root)

_log = logging.getLogger("DataModule")

get_db_connection = None
update_lotto_data = None
LottoRepository = None
MLModelRepository = None

# 1. Safe import of database connection helper
try:
    from data.database import get_db_connection
except ImportError:
    try:
        from .database import get_db_connection
    except ImportError as e:
        _log.warning(f"[DataModule] Could not import 'get_db_connection': {e}")

# 2. Safe import of lotto data updater
try:
    from data.updater import update_lotto_data
except ImportError:
    try:
        from .updater import update_lotto_data
    except ImportError as e:
        _log.warning(f"[DataModule] Could not import 'update_lotto_data': {e}")

# 3. Safe imports of repositories
try:
    from data.repositories.lotto_repository import LottoRepository
    from data.repositories.ml_model_repository import MLModelRepository
except ImportError:
    try:
        from .repositories.lotto_repository import LottoRepository
        from .repositories.ml_model_repository import MLModelRepository
    except ImportError as e:
        _log.warning(f"[DataModule] Could not import repositories: {e}")

_log.info("[DataModule] Data package initialization completed.")

__all__ = [
    "get_db_connection",
    "update_lotto_data",
    "LottoRepository",
    "MLModelRepository",
]