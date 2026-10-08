# -*- coding: utf-8 -*-
# data/database.py
import sqlite3
import os
import sys
import logging
import threading
from contextlib import contextmanager
from typing import Generator

# Ensure project root is in sys.path and initialize centralized logging
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir) if "data" in current_dir else current_dir
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.logger import setup_logging
setup_logging(project_root)

_log = logging.getLogger("Database")

# Ensure absolute DB storage path inside the 'db/' folder at project root, unified to 'lottomater.db'
PROJECT_ROOT = project_root
DB_DIR = os.path.join(PROJECT_ROOT, "db")
DB_PATH = os.path.join(DB_DIR, "lottomater.db")

# Thread-local storage to maintain independent database connections per thread (Thread-Safe)
_thread_local = threading.local()


def get_db_connection() -> sqlite3.Connection:
    """
    Creates and returns a thread-local SQLite database connection object linked to the unified master lottomater.db.
    Applies absolute paths, WAL concurrency mode, foreign key enforcement, and extended connection timeouts.
    Ensures safe multi-threaded execution across UI and background worker threads.
    """
    os.makedirs(DB_DIR, exist_ok=True)
    
    conn = getattr(_thread_local, "connection", None)
    
    # Check if connection exists and is still responsive
    is_valid = False
    if conn is not None:
        try:
            conn.execute("SELECT 1;")
            is_valid = True
        except Exception:
            is_valid = False
            try:
                conn.close()
            except Exception:
                pass
            _thread_local.connection = None

    if not is_valid:
        try:
            conn = sqlite3.connect(DB_PATH, timeout=30.0)
            # Set row_factory to receive query results as dictionary-like Row objects
            conn.row_factory = sqlite3.Row
            
            # Optimize performance and concurrency for multi-threaded access
            cursor = conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("PRAGMA foreign_keys=ON;")
            cursor.close()
            
            _thread_local.connection = conn
            _log.debug(f"Successfully created thread-local DB connection for thread ID [{threading.get_ident()}] at: {DB_PATH}")
        except Exception as e:
            _log.error(f"Failed to connect to SQLite database at '{DB_PATH}': {e}", exc_info=True)
            raise
            
    return _thread_local.connection


@contextmanager
def get_db_cursor() -> Generator[sqlite3.Cursor, None, None]:
    """
    Context manager that provides a database cursor within a managed transaction block.
    Automatically commits on success or rolls back on exception, ensuring thread safety.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        _log.error(f"Database transaction rolled back due to error: {e}", exc_info=True)
        raise
    finally:
        cursor.close()


def close_db_connection():
    """
    Safely closes the database connection belonging to the current thread, if active.
    """
    conn = getattr(_thread_local, "connection", None)
    if conn is not None:
        try:
            conn.close()
            _log.debug(f"Closed thread-local DB connection for thread ID [{threading.get_ident()}].")
        except Exception as ex:
            _log.warning(f"Error while closing thread-local DB connection: {ex}", exc_info=True)
        finally:
            _thread_local.connection = None