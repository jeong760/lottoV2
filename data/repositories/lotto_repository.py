# data/repositories/lotto_repository.py
import sqlite3
import os
import sys
import logging
import json
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# Ensure project root is in sys.path and initialize centralized logging
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir)) if "repositories" in current_dir else current_dir
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.logger import setup_logging
setup_logging(project_root)
from utils.audit_security import AuditTrailSecurity
from data.draw_statistics import extract_draw_statistics

_log = logging.getLogger("LottoRepository")


class LottoRepository:
    """
    Unified Repository for lottomater.db supporting complete 1st~5th prize details, 
    winner counts, total sales, historical variable prize preservation, and cryptographic audit signatures.
    """
    _lock = threading.Lock()

    @staticmethod
    def _get_db_path() -> str:
        current_script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_script_dir))
        db_dir = os.path.join(project_root, "db")
        if not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        return os.path.join(db_dir, "lottomater.db")

    @classmethod
    def init_table(cls):
        """Initializes tables with full 1st~5th prize details, winner counts, and cryptographic signature support."""
        with cls._lock:
            conn = None
            try:
                conn = sqlite3.connect(cls._get_db_path(), timeout=30.0)
                cursor = conn.cursor()
                cursor.execute("PRAGMA journal_mode=WAL;")
                cursor.execute("PRAGMA foreign_keys=ON;")
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS lotto_draws (
                        draw_no INTEGER PRIMARY KEY,
                        draw_date TEXT,
                        num1 INTEGER, num2 INTEGER, num3 INTEGER,
                        num4 INTEGER, num5 INTEGER, num6 INTEGER,
                        bonus INTEGER,
                        tot_sellamnt INTEGER DEFAULT 0,
                        first_accumamnt INTEGER DEFAULT 0,
                        first_przwner_co INTEGER DEFAULT 0,
                        first_winamnt INTEGER DEFAULT 0,
                        second_accumamnt INTEGER DEFAULT 0,
                        second_przwner_co INTEGER DEFAULT 0,
                        second_winamnt INTEGER DEFAULT 0,
                        third_accumamnt INTEGER DEFAULT 0,
                        third_przwner_co INTEGER DEFAULT 0,
                        third_winamnt INTEGER DEFAULT 0,
                        fourth_accumamnt INTEGER DEFAULT 0,
                        fourth_przwner_co INTEGER DEFAULT 0,
                        fourth_winamnt INTEGER DEFAULT 0,
                        fifth_accumamnt INTEGER DEFAULT 0,
                        fifth_przwner_co INTEGER DEFAULT 0,
                        fifth_winamnt INTEGER DEFAULT 0
                    )
                """)

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS lotto_history (
                        drwNo INTEGER PRIMARY KEY,
                        drwNoDate TEXT,
                        drwtNo1 INTEGER, drwtNo2 INTEGER, drwtNo3 INTEGER,
                        drwtNo4 INTEGER, drwtNo5 INTEGER, drwtNo6 INTEGER,
                        bnusNo INTEGER,
                        totSellamnt INTEGER DEFAULT 0,
                        firstAccumamnt INTEGER DEFAULT 0,
                        firstPrzwnerCo INTEGER DEFAULT 0,
                        firstWinamnt INTEGER DEFAULT 0,
                        secondAccumamnt INTEGER DEFAULT 0,
                        secondPrzwnerCo INTEGER DEFAULT 0,
                        secondWinamnt INTEGER DEFAULT 0,
                        thirdAccumamnt INTEGER DEFAULT 0,
                        thirdPrzwnerCo INTEGER DEFAULT 0,
                        thirdWinamnt INTEGER DEFAULT 0,
                        fourthAccumamnt INTEGER DEFAULT 0,
                        fourthPrzwnerCo INTEGER DEFAULT 0,
                        fourthWinamnt INTEGER DEFAULT 0,
                        fifthAccumamnt INTEGER DEFAULT 0,
                        fifthPrzwnerCo INTEGER DEFAULT 0,
                        fifthWinamnt INTEGER DEFAULT 0
                    )
                """)

                required_cols = [
                    ("tot_sellamnt", "INTEGER DEFAULT 0"),
                    ("first_accumamnt", "INTEGER DEFAULT 0"), ("first_przwner_co", "INTEGER DEFAULT 0"), ("first_winamnt", "INTEGER DEFAULT 0"),
                    ("second_accumamnt", "INTEGER DEFAULT 0"), ("second_przwner_co", "INTEGER DEFAULT 0"), ("second_winamnt", "INTEGER DEFAULT 0"),
                    ("third_accumamnt", "INTEGER DEFAULT 0"), ("third_przwner_co", "INTEGER DEFAULT 0"), ("third_winamnt", "INTEGER DEFAULT 0"),
                    ("fourth_accumamnt", "INTEGER DEFAULT 0"), ("fourth_przwner_co", "INTEGER DEFAULT 0"), ("fourth_winamnt", "INTEGER DEFAULT 0"),
                    ("fifth_accumamnt", "INTEGER DEFAULT 0"), ("fifth_przwner_co", "INTEGER DEFAULT 0"), ("fifth_winamnt", "INTEGER DEFAULT 0")
                ]
                for col_name, col_type in required_cols:
                    try:
                        cursor.execute(f"ALTER TABLE lotto_draws ADD COLUMN {col_name} {col_type};")
                    except sqlite3.OperationalError:
                        pass
                    try:
                        cursor.execute(f"ALTER TABLE lotto_history ADD COLUMN {col_name} {col_type};")
                    except sqlite3.OperationalError:
                        pass

                history_required_cols = [
                    ("totSellamnt", "INTEGER DEFAULT 0"),
                    ("firstAccumamnt", "INTEGER DEFAULT 0"), ("firstPrzwnerCo", "INTEGER DEFAULT 0"), ("firstWinamnt", "INTEGER DEFAULT 0"),
                    ("secondAccumamnt", "INTEGER DEFAULT 0"), ("secondPrzwnerCo", "INTEGER DEFAULT 0"), ("secondWinamnt", "INTEGER DEFAULT 0"),
                    ("thirdAccumamnt", "INTEGER DEFAULT 0"), ("thirdPrzwnerCo", "INTEGER DEFAULT 0"), ("thirdWinamnt", "INTEGER DEFAULT 0"),
                    ("fourthAccumamnt", "INTEGER DEFAULT 0"), ("fourthPrzwnerCo", "INTEGER DEFAULT 0"), ("fourthWinamnt", "INTEGER DEFAULT 0"),
                    ("fifthAccumamnt", "INTEGER DEFAULT 0"), ("fifthPrzwnerCo", "INTEGER DEFAULT 0"), ("fifthWinamnt", "INTEGER DEFAULT 0"),
                ]
                existing_history_cols = {row[1] for row in cursor.execute("PRAGMA table_info(lotto_history)")}
                for col_name, col_type in history_required_cols:
                    if col_name not in existing_history_cols:
                        cursor.execute(f"ALTER TABLE lotto_history ADD COLUMN {col_name} {col_type};")

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS generated_sets (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id INTEGER,
                        created_at TEXT,
                        round_info TEXT,
                        set_no INTEGER,
                        algorithm_title TEXT,
                        numbers TEXT,
                        match_count INTEGER DEFAULT 0,
                        probability_str TEXT,
                        num1 INTEGER, num2 INTEGER, num3 INTEGER,
                        num4 INTEGER, num5 INTEGER, num6 INTEGER,
                        bonus_no INTEGER,
                        signature TEXT
                    )
                """)

                for col, ctype in [("bonus_no", "INTEGER DEFAULT 0"), ("signature", "TEXT")]:
                    try:
                        cursor.execute(f"ALTER TABLE generated_sets ADD COLUMN {col} {ctype};")
                    except sqlite3.OperationalError:
                        pass

                conn.commit()
            except Exception as e:
                _log.error(f"LottoRepository initialization exception: {e}", exc_info=True)
            finally:
                if conn:
                    conn.close()

    @classmethod
    def get_latest_draw_no(cls) -> int:
        cls.init_table()
        with cls._lock:
            conn = None
            try:
                conn = sqlite3.connect(cls._get_db_path(), timeout=30.0)
                cursor = conn.cursor()
                cursor.execute("SELECT MAX(draw_no) FROM lotto_draws")
                row = cursor.fetchone()
                return int(row[0]) if row and row[0] is not None else 0
            except Exception as e:
                _log.error(f"Failed to get latest draw number: {e}", exc_info=True)
                return 0
            finally:
                if conn:
                    conn.close()

    @classmethod
    def get_all_draws(cls) -> list[dict[str, Any]]:
        cls.init_table()
        with cls._lock:
            conn = None
            try:
                conn = sqlite3.connect(cls._get_db_path(), timeout=30.0)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM lotto_draws ORDER BY draw_no ASC")
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
            except Exception as e:
                _log.error(f"Exception occurred while retrieving historical winning data: {e}", exc_info=True)
                return []
            finally:
                if conn:
                    conn.close()

    @classmethod
    def save_draw(cls, draw_dict: dict[str, Any]):
        cls.save_draws_batch([draw_dict])

    @classmethod
    def save_draws_batch(cls, draw_dicts: list[dict[str, Any]]):
        if not draw_dicts:
            return

        cls.init_table()
        with cls._lock:
            conn = None
            try:
                conn = sqlite3.connect(cls._get_db_path(), timeout=30.0)
                cursor = conn.cursor()

                for draw_dict in draw_dicts:
                    drw_no = (
                        draw_dict.get("drawNo") or 
                        draw_dict.get("drwNo") or 
                        draw_dict.get("no") or 
                        draw_dict.get("draw_no") or 0
                    )
                    if not drw_no:
                        continue

                    base_date = datetime(2002, 12, 7)
                    calculated_date = (base_date + timedelta(weeks=int(drw_no) - 1)).strftime("%Y-%m-%d")
                    raw_date = draw_dict.get("date") or draw_dict.get("drwNoDate") or draw_dict.get("draw_date") or ""
                    drw_date = str(raw_date) if raw_date and str(raw_date).startswith("20") else calculated_date

                    nums = draw_dict.get("numbers") or []
                    if not nums:
                        for i in range(1, 7):
                            val = draw_dict.get(f"drwtNo{i}") or draw_dict.get(f"num{i}") or draw_dict.get(f"number{i}") or 0
                            if val:
                                nums.append(int(val))

                    valid_nums = [int(n) for n in nums if isinstance(n, (int, float, str)) and str(n).isdigit() and 1 <= int(n) <= 45]
                    sorted_nums = sorted(list(set(valid_nums)))
                    if len(sorted_nums) < 6:
                        continue

                    bonus = int(
                        draw_dict.get("bonusNo") or 
                        draw_dict.get("bnusNo") or 
                        draw_dict.get("bonus") or 
                        draw_dict.get("bonus_no") or 0
                    )

                    total_sales, prize_stats = extract_draw_statistics(draw_dict, int(drw_no))
                    tot_sell = total_sales or 0
                    prize_stats = prize_stats or [(0, 0, 0)] * 5

                    cursor.execute("""
                        INSERT OR REPLACE INTO lotto_draws (
                            draw_no, draw_date, num1, num2, num3, num4, num5, num6, bonus,
                            tot_sellamnt, 
                            first_accumamnt, first_przwner_co, first_winamnt, 
                            second_accumamnt, second_przwner_co, second_winamnt, 
                            third_accumamnt, third_przwner_co, third_winamnt, 
                            fourth_accumamnt, fourth_przwner_co, fourth_winamnt, 
                            fifth_accumamnt, fifth_przwner_co, fifth_winamnt
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        int(drw_no), str(drw_date),
                        sorted_nums[0], sorted_nums[1], sorted_nums[2], sorted_nums[3], sorted_nums[4], sorted_nums[5],
                        int(bonus), int(tot_sell),
                        *(value for rank_stats in prize_stats for value in rank_stats),
                    ))

                    cursor.execute("""
                        INSERT OR REPLACE INTO lotto_history (
                            drwNo, drwNoDate, drwtNo1, drwtNo2, drwtNo3, drwtNo4, drwtNo5, drwtNo6, bnusNo,
                            totSellamnt, 
                            firstAccumamnt, firstPrzwnerCo, firstWinamnt, 
                            secondAccumamnt, secondPrzwnerCo, secondWinamnt, 
                            thirdAccumamnt, thirdPrzwnerCo, thirdWinamnt, 
                            fourthAccumamnt, fourthPrzwnerCo, fourthWinamnt, 
                            fifthAccumamnt, fifthPrzwnerCo, fifthWinamnt
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        int(drw_no), str(drw_date),
                        sorted_nums[0], sorted_nums[1], sorted_nums[2], sorted_nums[3], sorted_nums[4], sorted_nums[5],
                        int(bonus), int(tot_sell),
                        *(value for rank_stats in prize_stats for value in rank_stats),
                    ))

                conn.commit()
            except Exception as e:
                _log.error(f"Failed to save draw batch: {e}", exc_info=True)
            finally:
                if conn:
                    conn.close()

    @classmethod
    def save_generation_history(cls, set_count: int, generated_sets: list, metadata: dict = None):
        cls.init_table()
        with cls._lock:
            conn = None
            try:
                conn = sqlite3.connect(cls._get_db_path(), timeout=30.0)
                cursor = conn.cursor()
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                session_id = int(datetime.now().timestamp() * 1000000)
                round_info = str(metadata.get("round", "Next") if metadata else "Next")
                algo_title = str(metadata.get("algorithm_title", metadata.get("algorithm", "AI Hybrid Engine")) if metadata else "AI Hybrid Engine")

                for idx, item in enumerate(generated_sets, 1):
                    bonus_no = 0
                    if isinstance(item, dict):
                        nums = item.get("numbers") or item.get("set_numbers") or []
                        bonus_no = int(item.get("bonus", item.get("bonus_no", 0)) or 0)
                        prob = item.get("probability", "N/A")
                    elif isinstance(item, (list, tuple)):
                        if len(item) == 7:
                            nums = item[:6]
                            bonus_no = int(item[6])
                        else:
                            nums = item
                        prob = "N/A"
                    else:
                        nums = []
                        prob = "N/A"

                    if isinstance(nums, (list, tuple)) and len(nums) >= 6:
                        valid_nums = [int(n) for n in nums[:6] if isinstance(n, (int, float, str)) and str(n).isdigit() and 1 <= int(n) <= 45]
                        if len(valid_nums) >= 6:
                            s_nums = sorted(valid_nums[:6])
                            nums_json = json.dumps(s_nums)
                            
                            signed_record = AuditTrailSecurity.create_signed_record(
                                numbers=s_nums,
                                metadata={
                                    "session_id": session_id,
                                    "round_info": round_info,
                                    "algorithm_title": algo_title,
                                    "set_no": idx
                                },
                                ensemble_contributions=[{"algorithm": algo_title, "weight": 1.0}]
                            )
                            signature = signed_record.get("signature", "")

                            cursor.execute("""
                                INSERT INTO generated_sets (
                                    session_id, created_at, round_info, set_no, algorithm_title,
                                    numbers, probability_str, num1, num2, num3, num4, num5, num6, bonus_no, signature
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                session_id, now_str, round_info, idx, algo_title,
                                nums_json, str(prob), s_nums[0], s_nums[1], s_nums[2], s_nums[3], s_nums[4], s_nums[5], bonus_no, signature
                            ))
                conn.commit()
            except Exception as e:
                _log.error(f"Failed to save generation history: {e}", exc_info=True)
            finally:
                if conn:
                    conn.close()

    @classmethod
    def get_generation_history(cls) -> list[dict[str, Any]]:
        cls.init_table()
        with cls._lock:
            conn = None
            try:
                conn = sqlite3.connect(cls._get_db_path(), timeout=30.0)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM generated_sets ORDER BY id DESC LIMIT 500")
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
            except Exception as e:
                _log.error(f"Failed to retrieve generation history: {e}", exc_info=True)
                return []
            finally:
                if conn:
                    conn.close()