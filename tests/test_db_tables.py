# tests/test_db_tables.py
import sys
import os
import logging
import pytest

# Ensure project root is in sys.path and initialize centralized logging
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir) if "tests" in current_dir else current_dir
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.logger import setup_logging
setup_logging(project_root)

_log = logging.getLogger("TestDBTables")

from data.database import get_db_connection, close_db_connection
from data.repositories.lotto_repository import LottoRepository


def test_database_connection_and_query():
    """Verify database connection object creation and basic query execution."""
    _log.info("Running test_database_connection_and_query...")
    try:
        # Use thread-local connection directly without 'with' statement to avoid premature closure
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        _log.debug(f"Tables retrieved from database: {tables}")
        assert isinstance(tables, list)
    except Exception as e:
        _log.error(f"Database connection or query failed: {e}", exc_info=True)
        pytest.fail(f"Database connection or query failed: {e}")
    finally:
        close_db_connection()


def test_repository_draws_fetch():
    """Verify data retrieval functionality through LottoRepository with table initialization."""
    _log.info("Running test_repository_draws_fetch...")
    try:
        # Ensure tables are initialized before fetching
        LottoRepository.init_table()
        
        draws = LottoRepository.get_all_draws()
        _log.debug(f"Successfully fetched draws count: {len(draws) if draws else 0}")
        assert isinstance(draws, list)
    except Exception as e:
        _log.error(f"Draws fetch raised an unexpected exception: {e}", exc_info=True)
        pytest.fail(f"Draws fetch failed: {e}")