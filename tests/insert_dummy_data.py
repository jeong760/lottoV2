# -*- coding: utf-8 -*-
# tests/test_db_cleanup.py
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

_log = logging.getLogger("TestDBCleanup")

# Safe import with fallback for LottoDBHelper location
LottoDBHelper = None
try:
    from core.lotto_db_helper import LottoDBHelper
except ImportError:
    try:
        from data.lotto_db_helper import LottoDBHelper
    except ImportError:
        pass

def run_test_with_cleanup():
    if not LottoDBHelper:
        _log.error("Error: LottoDBHelper could not be imported from core or data package.")
        print("❌ Error: LottoDBHelper could not be imported.")
        return

    db_path = LottoDBHelper._get_db_path() if hasattr(LottoDBHelper, "_get_db_path") else os.path.join(project_root, "db", "lottomater.db")
    _log.info(f"Target Database Path: {db_path}")
    print(f"Target Database Path: {db_path}")
    
    # 1. Insert temporary dummy generation history
    dummy_sets = [
        [3, 12, 24, 31, 38, 45, 7],
        [5, 14, 22, 29, 36, 42, 19]
    ]
    metadata = {"algorithm_title": "Temporary Test Algorithm"}
    
    _log.info("Inserting temporary dummy data into DB...")
    print("-> Inserting temporary dummy data into DB...")
    LottoDBHelper.save_generation_history(set_count=2, generated_sets=dummy_sets, metadata=metadata)
    
    # 2. Verify that the data was successfully loaded
    history = LottoDBHelper.get_generation_history() or []
    _log.info(f"Loaded records count (with dummy): {len(history)}")
    print(f"-> Loaded records count (with dummy): {len(history)}")
    
    # 3. Clean up: Delete the temporary dummy data to keep the database clean
    _log.info("Cleaning up (deleting temporary dummy data)...")
    print("-> Cleaning up (deleting temporary dummy data)...")
    conn = None
    try:
        conn = sqlite3.connect(db_path, timeout=10.0)
        cursor = conn.cursor()
        
        # Ensure foreign key constraints are enforced for cascading deletes
        cursor.execute("PRAGMA foreign_keys = ON;")
        
        # Delete sessions created by the test algorithm title
        cursor.execute("DELETE FROM generation_sessions WHERE algorithm_title = ?", ("Temporary Test Algorithm",))
        conn.commit()
    except Exception as e:
        _log.error(f"Error during cleanup: {e}", exc_info=True)
        print(f"❌ Error during cleanup: {e}")
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass
    
    # 4. Verify cleanup results
    history_after_cleanup = LottoDBHelper.get_generation_history() or []
    _log.info(f"Loaded records count after cleanup: {len(history_after_cleanup)}")
    print(f"-> Loaded records count after cleanup: {len(history_after_cleanup)}")
    _log.info("Test and database cleanup completed successfully!")
    print("✨ Test and database cleanup completed successfully!")

if __name__ == "__main__":
    run_test_with_cleanup()