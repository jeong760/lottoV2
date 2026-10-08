# -*- coding: utf-8 -*-
# test_db_inspect.py
import sys
import os
import sqlite3
import logging

# Ensure project root is in sys.path and initialize centralized logging
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir) if "tests" in current_dir else current_dir
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.logger import setup_logging
setup_logging(project_root)

_log = logging.getLogger("TestDBInspect")

# Safe import with fallback for LottoDBHelper location
LottoDBHelper = None
try:
    from core.lotto_db_helper import LottoDBHelper
except ImportError:
    try:
        from data.lotto_db_helper import LottoDBHelper
    except ImportError:
        pass

db_path = LottoDBHelper._get_db_path() if LottoDBHelper and hasattr(LottoDBHelper, "_get_db_path") else os.path.join(project_root, "db", "lottomater.db")
_log.info(f"Target Database Path: {db_path}")
print(f"Target Database Path: {db_path}")

if not os.path.exists(db_path):
    _log.error("Error: Database file does not exist at this path!")
    print("❌ Error: Database file does not exist at this path!")
else:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Check existing tables in DB
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    existing_tables = [row[0] for row in cursor.fetchall()]
    print(f"📋 Tables found in DB: {existing_tables}")

    # Check generation_sessions table if exists
    if "generation_sessions" in existing_tables:
        print("\n--- [Table: generation_sessions] ---")
        _log.info("Inspecting table: generation_sessions")
        try:
            cursor.execute("SELECT * FROM generation_sessions ORDER BY id DESC LIMIT 10")
            sessions = cursor.fetchall()
            print(f"Total rows (showing latest 10): {len(sessions)}")
            for s in sessions:
                print(dict(s))
        except Exception as e:
            _log.error(f"Error reading generation_sessions: {e}", exc_info=True)
            print(f"❌ Error reading generation_sessions: {e}")
    else:
        print("\n--- [Table: generation_sessions] (Not Found) ---")

    # Check generated_sets table if exists
    if "generated_sets" in existing_tables:
        print("\n--- [Table: generated_sets] ---")
        _log.info("Inspecting table: generated_sets")
        try:
            cursor.execute("SELECT * FROM generated_sets ORDER BY id DESC LIMIT 10")
            sets = cursor.fetchall()
            print(f"Total rows (showing latest 10): {len(sets)}")
            for st in sets:
                print(dict(st))
        except Exception as e:
            _log.error(f"Error reading generated_sets: {e}", exc_info=True)
            print(f"❌ Error reading generated_sets: {e}")
    else:
        print("\n--- [Table: generated_sets] (Not Found) ---")

    conn.close()
    _log.info("Database inspection completed successfully.")
    print("\n✨ Database inspection completed successfully.")