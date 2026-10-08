# -*- coding: utf-8 -*-
# data/updater.py
import json
import requests
import sys
import os
import logging
from typing import Dict, Any, List

# Ensure project root is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir) if "data" in current_dir else current_dir
if project_root not in sys.path:
    sys.path.insert(0, project_root)

_log = logging.getLogger("LottoUpdater")

from data.repositories.lotto_repository import LottoRepository

LOTTO_JSON_URL = "https://raw.githubusercontent.com/jeong760/lotto-data/main/data/lotto-history.json"


def get_draw_no(draw: dict) -> int:
    """Flexibly extracts draw number keys from various dictionary formats safely."""
    if not isinstance(draw, dict):
        return 0
    for key in ["drwNo", "drw_no", "no", "drawNo", "draw_no"]:
        if key in draw and draw[key] is not None:
            try:
                return int(draw[key])
            except (ValueError, TypeError):
                continue
    return 0


def update_lotto_data() -> Dict[str, Any]:
    """
    Fetches official lotto history records exclusively from remote JSON source.
    Updates SQLite DB directly with complete history records and returns synchronization metrics.
    """
    _log.info("Inspecting local lotto database state...")
    
    result_summary = {
        "status": "failed",
        "added_count": 0,
        "synced_count": 0,
        "latest_draw": 0,
        "message": ""
    }

    # 1. Initialize SQLite database tables safely
    try:
        LottoRepository.init_table()
    except Exception as e:
        _log.warning(f"Table initialization warning: {e}", exc_info=True)
    
    # 2. Check current local DB latest draw number
    local_latest_no = LottoRepository.get_latest_draw_no()
    _log.info(f"Current local DB latest draw: #{local_latest_no}")
    
    raw_list = []
    
    # 3. Fetch latest lotto data directly from remote primary JSON source
    try:
        _log.info(f"Fetching latest lotto draw records from remote source: {LOTTO_JSON_URL}")
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
        else:
            _log.warning(f"Remote server responded with status code: {response.status_code}")
    except requests.exceptions.RequestException as net_ex:
        _log.warning(f"Network warning during remote fetch: {net_ex}")
    except Exception as e:
        _log.error(f"Exception during remote fetch: {e}", exc_info=True)
        result_summary["message"] = str(e)
        return result_summary

    # 4. Parse raw list records into clean dictionaries safely
    lotto_list = []
    for item in raw_list:
        if isinstance(item, str):
            try:
                item = json.loads(item)
            except Exception:
                continue
        if isinstance(item, dict):
            lotto_list.append(item)

    if not lotto_list:
        _log.warning("No valid lotto records retrieved from remote source.")
        result_summary["message"] = "No valid records retrieved."
        return result_summary

    # 5. Save/Sync fetched history records into SQLite DB with batch optimization if supported
    added_count = 0
    synced_count = 0

    try:
        # Check if repository supports bulk save method for optimized performance
        if hasattr(LottoRepository, "save_draws_batch") and callable(getattr(LottoRepository, "save_draws_batch")):
            formatted_draws = []
            for draw in lotto_list:
                drw_no = get_draw_no(draw)
                if drw_no > 0:
                    if "drwNo" not in draw:
                        draw["drwNo"] = drw_no
                    formatted_draws.append(draw)
            
            if formatted_draws:
                LottoRepository.save_draws_batch(formatted_draws)
                for draw in formatted_draws:
                    drw_no = get_draw_no(draw)
                    if drw_no > local_latest_no:
                        added_count += 1
                    else:
                        synced_count += 1
        else:
            # Fallback to individual iterative saving with error handling
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
                        _log.error(f"Failed to save draw #{drw_no}: {save_err}", exc_info=True)
                        
    except Exception as batch_err:
        _log.error(f"Error during lotto database synchronization batch: {batch_err}", exc_info=True)

    final_db_max = LottoRepository.get_latest_draw_no()
    
    _log.info("--------------------------------------------------")
    _log.info("Database Synchronization Completed!")
    _log.info(f" - New Draws Inserted : {added_count}")
    _log.info(f" - Synced Existing    : {synced_count}")
    _log.info(f" - Latest DB Draw     : #{final_db_max}")
    _log.info("--------------------------------------------------")

    result_summary["status"] = "success"
    result_summary["added_count"] = added_count
    result_summary["synced_count"] = synced_count
    result_summary["latest_draw"] = final_db_max
    result_summary["message"] = "Synchronization successful."
    return result_summary


if __name__ == "__main__":
    from utils.logger import setup_logging
    setup_logging(project_root)
    update_lotto_data()