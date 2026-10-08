# data/updater.py
import json
import requests
import sys
import os
import logging

# Ensure project root is in python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.repositories.lotto_repository import LottoRepository

_log = logging.getLogger("LottoUpdater")

LOTTO_JSON_URL = "https://raw.githubusercontent.com/jeong760/lotto-data/main/data/lotto-history.json"


def get_draw_no(draw: dict) -> int:
    """Flexibly extracts draw number keys from various dictionary formats."""
    if not isinstance(draw, dict):
        return 0
    for key in ["drwNo", "drw_no", "no", "drawNo", "draw_no"]:
        if key in draw and draw[key] is not None:
            try:
                return int(draw[key])
            except (ValueError, TypeError):
                continue
    return 0


def update_lotto_data():
    """
    Fetches official lotto history records exclusively from remote JSON source.
    Updates SQLite DB directly with complete history records.
    """
    print("Inspecting local lotto database state...")
    
    # 1. Initialize SQLite database tables
    try:
        LottoRepository.init_table()
    except Exception as e:
        _log.warning(f"Table initialization warning: {e}")
    
    # 2. Check current local DB latest draw number
    local_latest_no = LottoRepository.get_latest_draw_no()
    print(f"Current local DB latest draw: #{local_latest_no}")
    
    raw_list = []
    
    # 3. Fetch latest lotto data directly from remote primary JSON source
    try:
        print("Fetching latest lotto draw records from remote JSON source...")
        response = requests.get(LOTTO_JSON_URL, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                raw_list = data
            elif isinstance(data, dict):
                for key in ["data", "result", "list", "draws", "history"]:
                    if key in data and isinstance(data[key], list):
                        raw_list = data[key]
                        break
                if not raw_list:
                    for val in data.values():
                        if isinstance(val, list):
                            raw_list = val
                            break
    except requests.exceptions.RequestException as net_ex:
        print(f"Network warning during remote fetch: {net_ex}.")
    except Exception as e:
        print(f"Exception during remote fetch: {e}")

    # 4. Parse raw list records into clean dictionaries
    lotto_list = []
    for item in raw_list:
        if isinstance(item, str):
            try:
                item = json.loads(item)
            except Exception:
                continue
        if isinstance(item, dict):
            lotto_list.append(item)

    # 5. Save/Sync fetched history records into SQLite DB
    added_count = 0
    synced_count = 0

    if lotto_list:
        for draw in lotto_list:
            drw_no = get_draw_no(draw)
            if drw_no > 0:
                if "drwNo" not in draw:
                    draw["drwNo"] = drw_no
                
                try:
                    LottoRepository.save_draw(draw)
                    if drw_no > local_latest_no:
                        added_count += 1
                    else:
                        synced_count += 1
                except Exception as save_err:
                    _log.error(f"Failed to save draw #{drw_no}: {save_err}")

    final_db_max = LottoRepository.get_latest_draw_no()
    
    print("--------------------------------------------------")
    print(f"Database Synchronization Completed!")
    print(f" - New Draws Inserted : {added_count}")
    print(f" - Synced Existing    : {synced_count}")
    print(f" - Latest DB Draw     : #{final_db_max}")
    print("--------------------------------------------------")


if __name__ == "__main__":
    update_lotto_data()