# tests/test_load_history.py
import sys
import os
import logging

# Ensure project root is in sys.path and initialize centralized logging
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir) if "tests" in current_dir else current_dir
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.logger import setup_logging
setup_logging(project_root)

_log = logging.getLogger("TestLoadHistory")

# Safe import with fallback for LottoDBHelper location
LottoDBHelper = None
try:
    from core.lotto_db_helper import LottoDBHelper
except ImportError:
    try:
        from data.lotto_db_helper import LottoDBHelper
    except ImportError:
        pass

def check_generation_history():
    if not LottoDBHelper:
        _log.error("Error: LottoDBHelper could not be imported from core or data package.")
        print("❌ Error: LottoDBHelper could not be imported.")
        return

    _log.info("Fetching generation history using LottoDBHelper...")
    print("-> Fetching generation history using LottoDBHelper...")
    try:
        history = LottoDBHelper.get_generation_history() or []
        _log.info(f"Successfully loaded {len(history)} generation history records.")
        print(f"📊 Total Sessions / Sets Found: {len(history)}")
        
        # Display sample records if available
        if history:
            print("\n--- Recent Generation History Sample ---")
            for idx, record in enumerate(history[:3], 1):
                print(f"  [{idx}] ID: {record.get('id')} | Algorithm: {record.get('algorithm_title')} | Numbers: {record.get('numbers')}")
    except Exception as e:
        _log.error(f"Error retrieving generation history: {e}", exc_info=True)
        print(f"❌ Error retrieving generation history: {e}")

if __name__ == "__main__":
    check_generation_history()