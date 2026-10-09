# data/lotto_db_helper.py
import sqlite3
import os
import sys
import logging
import threading
import json
from datetime import datetime, timedelta, timezone

# Ensure project root is in sys.path and initialize centralized logging
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir) if "data" in current_dir else current_dir
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.logger import setup_logging
setup_logging(project_root)

_log = logging.getLogger("LottoDBHelper")

try:
    from data.lotto_evaluator import LottoEvaluator
except ImportError:
    from core.lotto_evaluator import LottoEvaluator


class LottoDBHelper:
    """
    Unified history management for db/lottomater.db supporting 
    both relational set details and JSON-serialized structures with thread safety.
    Focused purely on data persistence and retrieval, delegating evaluation to LottoEvaluator.
    """
    _lock = threading.RLock()

    @staticmethod
    def _get_db_path() -> str:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        db_dir = os.path.join(project_root, "db")
        if not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        return os.path.join(db_dir, "lottomater.db")

    @staticmethod
    def _get_kst_now() -> str:
        """Returns current timestamp strictly formatted in Korea Standard Time (KST, UTC+9)."""
        kst = timezone(timedelta(hours=9))
        return datetime.now(kst).strftime("%Y-%m-%d %H:%M:%S")

    @classmethod
    def _backfill_generation_batch_ids_from_metadata(cls, cursor):
        """Backfills empty generation_batch_id column values from metadata_json for legacy rows."""
        try:
            cursor.execute("""
                SELECT id, metadata_json
                FROM generation_sessions
                WHERE (generation_batch_id IS NULL OR generation_batch_id = '')
                  AND metadata_json IS NOT NULL
                  AND metadata_json != ''
                  AND metadata_json != '{}'
            """)
            legacy_rows = cursor.fetchall()
        except Exception:
            legacy_rows = []

        if not legacy_rows:
            return

        updates = []
        for row in legacy_rows:
            try:
                session_id = int(row[0])
            except Exception:
                continue
            raw_meta = row[1]
            if not raw_meta:
                continue
            try:
                parsed = json.loads(raw_meta)
            except Exception:
                parsed = {}
            if not isinstance(parsed, dict):
                continue
            batch_id = str(parsed.get("generation_batch_id") or "").strip()
            if batch_id:
                updates.append((batch_id, session_id))

        if updates:
            try:
                cursor.executemany(
                    "UPDATE generation_sessions SET generation_batch_id = ? WHERE id = ?",
                    updates,
                )
            except Exception:
                pass

    @classmethod
    def _ensure_tables(cls):
        db_path = cls._get_db_path()
        with cls._lock:
            conn = None
            try:
                conn = sqlite3.connect(db_path, timeout=30.0)
                cursor = conn.cursor()
                cursor.execute("PRAGMA journal_mode=WAL;")
                cursor.execute("PRAGMA foreign_keys = ON;")
                
                # 1. Session table creation
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS generation_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        created_at TEXT,
                        set_count INTEGER,
                        algorithm_title TEXT,
                        round_info TEXT DEFAULT 'Live Draw',
                        metadata_json TEXT DEFAULT '{}',
                        generation_batch_id TEXT DEFAULT ''
                    )
                """)

                for col, ctype in [
                    ("round_info", "TEXT DEFAULT 'Live Draw'"),
                    ("metadata_json", "TEXT DEFAULT '{}'"),
                    ("generation_batch_id", "TEXT DEFAULT ''"),
                ]:
                    try:
                        cursor.execute(f"ALTER TABLE generation_sessions ADD COLUMN {col} {ctype}")
                    except sqlite3.OperationalError:
                        pass

                try:
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_generation_sessions_batch_id ON generation_sessions(generation_batch_id)")
                except sqlite3.OperationalError:
                    pass

                try:
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_generation_sessions_created_at ON generation_sessions(created_at)")
                except sqlite3.OperationalError:
                    pass
                 
                # 2. Unified generated_sets table creation
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
                        rounds_info TEXT DEFAULT '-',
                        probability_str TEXT,
                        num1 INTEGER, num2 INTEGER, num3 INTEGER,
                        num4 INTEGER, num5 INTEGER, num6 INTEGER,
                        bonus_no INTEGER,
                        FOREIGN KEY(session_id) REFERENCES generation_sessions(id) ON DELETE CASCADE
                    )
                """)

                # Safety migration fallback if rounds_info column does not exist
                try:
                    cursor.execute("ALTER TABLE generated_sets ADD COLUMN rounds_info TEXT DEFAULT '-'")
                except sqlite3.OperationalError:
                    pass

                try:
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_generated_sets_session_set_no ON generated_sets(session_id, set_no)")
                except sqlite3.OperationalError:
                    pass

                cls._backfill_generation_batch_ids_from_metadata(cursor)

                # 3. Official history tables creation
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS lotto_history (
                        drwNo INTEGER PRIMARY KEY,
                        drwNoDate TEXT,
                        drwtNo1 INTEGER, drwtNo2 INTEGER, drwtNo3 INTEGER,
                        drwtNo4 INTEGER, drwtNo5 INTEGER, drwtNo6 INTEGER,
                        bnusNo INTEGER
                    )
                """)

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS lotto_draws (
                        draw_no INTEGER PRIMARY KEY,
                        draw_date TEXT,
                        num1 INTEGER, num2 INTEGER, num3 INTEGER,
                        num4 INTEGER, num5 INTEGER, num6 INTEGER,
                        bonus INTEGER
                    )
                """)

                conn.commit()
            except Exception as e:
                if conn:
                    conn.rollback()
                _log.error(f"Error during LottoDBHelper table initialization: {e}", exc_info=True)
            finally:
                if conn:
                    conn.close()

    @classmethod
    def get_latest_winning_numbers(cls):
        """Fetches the latest official winning numbers and bonus number from the database."""
        draws = cls.get_all_draws()
        if draws:
            latest = max(draws, key=lambda x: x.get("draw_no", 0))
            winning_nums = [latest.get(f"num{i}") for i in range(1, 7)]
            bonus_no = latest.get("bonus", 0)
            return {n for n in winning_nums if n}, int(bonus_no) if bonus_no else 0
        
        history = cls.get_all_history_records()
        if history:
            latest = max(history, key=lambda x: x.get("draw_no", 0))
            winning_nums = latest.get("numbers", [])
            bonus_no = latest.get("bonus", 0)
            return {n for n in winning_nums if n}, int(bonus_no) if bonus_no else 0

        return set(), 0

    @classmethod
    def get_all_draws(cls) -> list:
        """Fetches all stored official draw records."""
        cls._ensure_tables()
        db_path = cls._get_db_path()
        draws = []
        with cls._lock:
            conn = None
            try:
                conn = sqlite3.connect(db_path, timeout=30.0)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT draw_no, draw_date, num1, num2, num3, num4, num5, num6, bonus FROM lotto_draws ORDER BY draw_no ASC")
                rows = cursor.fetchall()
                for row in rows:
                    draws.append(dict(row))
            except Exception as e:
                _log.error(f"Failed to fetch draws: {e}", exc_info=True)
            finally:
                if conn:
                    conn.close()
        return draws

    @classmethod
    def get_all_history_records(cls) -> list:
        """Fetches all actual historical winning draws (Required by AITrainWorker)."""
        cls._ensure_tables()
        db_path = cls._get_db_path()
        records = []
        with cls._lock:
            conn = None
            try:
                conn = sqlite3.connect(db_path, timeout=30.0)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT drwNo, drwNoDate, drwtNo1, drwtNo2, drwtNo3, drwtNo4, drwtNo5, drwtNo6, bnusNo 
                    FROM lotto_history ORDER BY drwNo ASC
                """)
                rows = cursor.fetchall()
                for row in rows:
                    nums = [row["drwtNo1"], row["drwtNo2"], row["drwtNo3"], row["drwtNo4"], row["drwtNo5"], row["drwtNo6"]]
                    if all(nums):
                        records.append({
                            "draw_no": row["drwNo"],
                            "date": row["drwNoDate"] or "2002-12-07",
                            "numbers": sorted([int(n) for n in nums]),
                            "bonus": row["bnusNo"]
                        })
            except Exception as e:
                _log.error(f"Failed to fetch historical winning records: {e}", exc_info=True)
            finally:
                if conn:
                    conn.close()
        return records

    @classmethod
    def evaluate_against_history(cls, generated_6_numbers: list, bonus_number: int, target_draw_no: int = None) -> tuple:
        """Delegates evaluation to LottoEvaluator."""
        history_draws = cls.get_all_history_records()
        if not history_draws:
            draws_alt = cls.get_all_draws()
            for d in draws_alt:
                nums = [d.get(f"num{i}") for i in range(1, 7)]
                history_draws.append({
                    "draw_no": d.get("draw_no"),
                    "numbers": [n for n in nums if n],
                    "bonus": d.get("bonus", 0)
                })
        return LottoEvaluator.evaluate(generated_6_numbers, bonus_number, history_draws, target_draw_no)

    @classmethod
    def save_generation_history(cls, set_count: int, generated_sets: list, metadata: dict = None, target_draw_no: int = None):
        """Saves newly generated number sets and session metadata to the local SQLite database."""
        cls._ensure_tables()
        db_path = cls._get_db_path()
        meta = metadata if isinstance(metadata, dict) else {}
        title = meta.get("algorithm_title") or meta.get("algorithm") or "Statistical Distribution Model"
        round_info = meta.get("round_info") or meta.get("round") or "Live Draw"
        generation_batch_id = str(meta.get("generation_batch_id") or "").strip()
        safe_meta = {}
        for key, value in meta.items():
            if value is None:
                safe_meta[key] = None
                continue
            try:
                json.dumps(value, ensure_ascii=False)
                safe_meta[key] = value
            except Exception:
                safe_meta[key] = str(value)

        safe_meta["algorithm_title"] = str(title)
        safe_meta["round_info"] = str(round_info)
        if generation_batch_id:
            safe_meta["generation_batch_id"] = generation_batch_id
        metadata_json = json.dumps(safe_meta, ensure_ascii=False, default=str)
        
        now_str = cls._get_kst_now()

        with cls._lock:
            conn = None
            try:
                conn = sqlite3.connect(db_path, timeout=30.0)
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO generation_sessions (created_at, set_count, algorithm_title, round_info, metadata_json, generation_batch_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (now_str, set_count, str(title), str(round_info), metadata_json, generation_batch_id))
                session_id = cursor.lastrowid

                for idx, raw_item in enumerate(generated_sets):
                    nums = raw_item.get("numbers", []) if isinstance(raw_item, dict) else raw_item

                    if not isinstance(nums, (list, tuple)) or len(nums) < 6:
                        continue
                    
                    base_nums = sorted([int(n) for n in nums[:6]])
                    bonus_val = int(nums[6]) if len(nums) >= 7 else 0
                    full_list_for_json = base_nums + ([bonus_val] if bonus_val else [])
                    numbers_json = json.dumps(full_list_for_json)

                    current_set_no = idx + 1
                    rounds_desc, evaluated_match_count = cls.evaluate_against_history(base_nums, bonus_val, target_draw_no)

                    cursor.execute("""
                        INSERT INTO generated_sets (
                            session_id, created_at, round_info, set_no, algorithm_title,
                            numbers, match_count, rounds_info, probability_str,
                            num1, num2, num3, num4, num5, num6, bonus_no
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        session_id, now_str, str(round_info), current_set_no, str(title),
                        numbers_json, evaluated_match_count, rounds_desc, "0.00%",
                        base_nums[0], base_nums[1], base_nums[2],
                        base_nums[3], base_nums[4], base_nums[5],
                        bonus_val if bonus_val else None
                    ))

                conn.commit()
            except Exception as e:
                if conn:
                    conn.rollback()
                _log.error(f"Failed to save generation history in LottoDBHelper: {e}", exc_info=True)
            finally:
                if conn:
                    conn.close()

    @staticmethod
    def _chunk_list(values: list, chunk_size: int = 900) -> list:
        values = values if isinstance(values, list) else []
        if not values:
            return []
        size = max(1, int(chunk_size))
        return [values[i:i + size] for i in range(0, len(values), size)]

    @classmethod
    def _propagate_batch_rank_metadata(cls, records: list) -> list:
        """Backfills shared ranking metadata across sessions from the same generation batch."""
        if not isinstance(records, list) or not records:
            return records

        batch_seed = {}
        for rec in records:
            meta = rec.get("metadata", {}) if isinstance(rec, dict) else {}
            if not isinstance(meta, dict):
                continue
            batch_id = str(meta.get("generation_batch_id", "") or "").strip()
            if not batch_id:
                continue

            ranked = meta.get("top_ranked_combinations")
            weights = meta.get("score_weight_profile")
            if isinstance(ranked, list) and ranked:
                batch_seed.setdefault(batch_id, {})["top_ranked_combinations"] = ranked
            if isinstance(weights, dict) and weights:
                batch_seed.setdefault(batch_id, {})["score_weight_profile"] = weights

        if not batch_seed:
            return records

        for rec in records:
            meta = rec.get("metadata", {}) if isinstance(rec, dict) else {}
            if not isinstance(meta, dict):
                continue
            batch_id = str(meta.get("generation_batch_id", "") or "").strip()
            if not batch_id or batch_id not in batch_seed:
                continue

            seed = batch_seed.get(batch_id, {})
            ranked = meta.get("top_ranked_combinations")
            weights = meta.get("score_weight_profile")
            if (not isinstance(ranked, list) or not ranked) and "top_ranked_combinations" in seed:
                meta["top_ranked_combinations"] = seed["top_ranked_combinations"]
            if (not isinstance(weights, dict) or not weights) and "score_weight_profile" in seed:
                meta["score_weight_profile"] = seed["score_weight_profile"]
            rec["metadata"] = meta

        return records

    @classmethod
    def _load_generation_history_internal(cls, max_sessions: int = None, session_ids: list = None) -> list:
        cls._ensure_tables()
        db_path = cls._get_db_path()
        records = []
        limit_value = None
        if max_sessions is not None:
            try:
                parsed = int(max_sessions)
                if parsed > 0:
                    limit_value = parsed
            except Exception:
                limit_value = None

        filtered_session_ids = []
        if isinstance(session_ids, (list, tuple, set)):
            seen = set()
            for raw in session_ids:
                try:
                    sid = int(raw)
                except Exception:
                    continue
                if sid > 0 and sid not in seen:
                    seen.add(sid)
                    filtered_session_ids.append(sid)
            filtered_session_ids.sort(reverse=True)

        with cls._lock:
            conn = None
            try:
                conn = sqlite3.connect(db_path, timeout=30.0)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                session_query = """
                    SELECT id, created_at, set_count, algorithm_title, round_info, metadata_json, generation_batch_id
                    FROM generation_sessions
                """
                session_params = []
                if filtered_session_ids:
                    placeholders = ",".join("?" * len(filtered_session_ids))
                    session_query += f" WHERE id IN ({placeholders})"
                    session_params.extend(filtered_session_ids)
                session_query += " ORDER BY id DESC"
                if limit_value is not None:
                    session_query += " LIMIT ?"
                    session_params.append(limit_value)

                cursor.execute(session_query, tuple(session_params))
                sessions = [dict(s) for s in cursor.fetchall()]

                if not sessions:
                    return []

                session_id_scope = []
                for s in sessions:
                    try:
                        sid = int(s.get("id", 0) or 0)
                    except Exception:
                        sid = 0
                    if sid > 0:
                        session_id_scope.append(sid)
                if not session_id_scope:
                    return []

                all_sets = []
                for sid_chunk in cls._chunk_list(session_id_scope, 900):
                    placeholders = ",".join("?" * len(sid_chunk))
                    cursor.execute(
                        f"""
                            SELECT session_id, set_no, numbers, match_count, rounds_info,
                                   num1, num2, num3, num4, num5, num6, bonus_no
                            FROM generated_sets
                            WHERE session_id IN ({placeholders})
                            ORDER BY session_id DESC, set_no ASC
                        """,
                        tuple(sid_chunk),
                    )
                    all_sets.extend(cursor.fetchall())

                # Group sets by session_id in memory
                sets_by_session = {sid: [] for sid in session_id_scope}
                for row in all_sets:
                    s_id = row["session_id"]
                    if s_id not in sets_by_session:
                        sets_by_session[s_id] = []
                     
                    nums = [row["num1"], row["num2"], row["num3"], row["num4"], row["num5"], row["num6"]]
                    safe_nums = []
                    for raw in nums:
                        if raw is None:
                            continue
                        try:
                            val = int(raw)
                        except Exception:
                            continue
                        if 1 <= val <= 45:
                            safe_nums.append(val)

                    if len(safe_nums) < 6 and row["numbers"]:
                        try:
                            parsed_nums = json.loads(row["numbers"])
                            if isinstance(parsed_nums, list):
                                for raw in parsed_nums[:6]:
                                    try:
                                        val = int(raw)
                                    except Exception:
                                        continue
                                    if 1 <= val <= 45:
                                        safe_nums.append(val)
                        except Exception:
                            pass

                    # keep order-stable de-dup and cap to 6 base numbers
                    dedup_nums = []
                    seen_num = set()
                    for val in safe_nums:
                        if val in seen_num:
                            continue
                        seen_num.add(val)
                        dedup_nums.append(val)
                        if len(dedup_nums) >= 6:
                            break
                     
                    bonus = row["bonus_no"] or 0
                    rounds_info = row["rounds_info"] if "rounds_info" in row.keys() else "-"

                    sets_by_session[s_id].append({
                        "set_no": row["set_no"] or 1,
                        "numbers": sorted(dedup_nums),
                        "bonus_no": int(bonus),
                        "match_count": row["match_count"] or 0,
                        "rounds_info": rounds_info if rounds_info else "-"
                    })

                for s in sessions:
                    session_id = s["id"]
                    sets_detail = sets_by_session.get(session_id, [])
                    session_title = s["algorithm_title"]
                    session_meta = {}
                    raw_meta = s["metadata_json"] if "metadata_json" in s.keys() else "{}"
                    if raw_meta:
                        try:
                            parsed_meta = json.loads(raw_meta)
                            if isinstance(parsed_meta, dict):
                                session_meta = parsed_meta
                        except Exception:
                            session_meta = {}

                    if "algorithm_title" not in session_meta:
                        session_meta["algorithm_title"] = session_title
                    if "round_info" not in session_meta:
                        session_meta["round_info"] = s["round_info"] if "round_info" in s.keys() else "Live Draw"
                    if "generation_batch_id" not in session_meta:
                        session_meta["generation_batch_id"] = str(s["generation_batch_id"]) if "generation_batch_id" in s.keys() and s["generation_batch_id"] is not None else ""

                    if not session_title or session_title == "Quality Gate Filtered Engine":
                        session_title = session_meta.get("algorithm_title", "Statistical Distribution Model")
                    if not session_title:
                        session_title = "Statistical Distribution Model"
                    session_meta["algorithm_title"] = session_title

                    records.append({
                        "session_id": session_id,
                        "created_at": s["created_at"],
                        "set_count": s["set_count"],
                        "sets_detail": sets_detail,
                        "metadata": session_meta
                    })
                return cls._propagate_batch_rank_metadata(records)
            except Exception as e:
                _log.error(f"Failed to load generation history: {e}", exc_info=True)
                return []
            finally:
                if conn:
                    conn.close()

    @classmethod
    def load_generation_history(cls, max_sessions: int = None, session_ids: list = None) -> list:
        """Loads raw generation sessions and set details from local DB with optional scoping."""
        return cls._load_generation_history_internal(max_sessions=max_sessions, session_ids=session_ids)

    @classmethod
    def get_generation_history(cls, max_sessions: int = None, session_ids: list = None) -> list:
        """Retrieves formatted and evaluated generation history records with match counts and probabilities."""
        records = cls.load_generation_history(max_sessions=max_sessions, session_ids=session_ids)
        flat_records = []
        winning_set, winning_bonus = cls.get_latest_winning_numbers()

        for rec in records:
            session_id = rec.get("session_id")
            created_at = rec.get("created_at")
            
            meta_title = rec.get("metadata", {}).get("algorithm_title")
            if not meta_title or meta_title == "Quality Gate Filtered Engine":
                meta_title = "Statistical Distribution Model"
            title = meta_title

            for s_detail in rec.get("sets_detail", []):
                nums = s_detail.get("numbers", [])
                bonus = s_detail.get("bonus_no", 0)
                full_numbers = list(nums) + ([int(bonus)] if bonus else [])

                match_count = s_detail.get("match_count", 0)
                rounds_info = s_detail.get("rounds_info", "-")

                has_bonus_match = winning_bonus > 0 and (bonus == winning_bonus or winning_bonus in nums)
                probability_str = LottoEvaluator.calculate_probability(match_count, has_bonus_match)

                set_no_val = s_detail.get('set_no', 1) - 1
                cycle = set_no_val // 26
                char_idx = set_no_val % 26
                letter = chr(ord('A') + char_idx)
                
                set_label = f"SET {letter}" if cycle == 0 else f"SET {letter}{cycle - 1}"

                flat_records.append({
                    "id": session_id,
                    "created_at": created_at,
                    "round_info": set_label,
                    "algorithm_title": title,
                    "numbers": full_numbers,
                    "match_count": match_count,
                    "rounds_info": rounds_info,
                    "probability_str": probability_str,
                    "session_metadata": rec.get("metadata", {}),
                    "top_ranked_combinations": rec.get("metadata", {}).get("top_ranked_combinations", []),
                    "score_weight_profile": rec.get("metadata", {}).get("score_weight_profile", {}),
                })
        return flat_records

    @classmethod
    def get_all_generation_history(cls, max_sessions: int = None, session_ids: list = None) -> list:
        """Retrieves all generation history formatted for external modules."""
        records = cls.load_generation_history(max_sessions=max_sessions, session_ids=session_ids)
        return [{
            "id": rec.get("session_id"),
            "timestamp": rec.get("created_at"),
            "algorithm_title": rec.get("metadata", {}).get("algorithm_title", "Statistical Distribution Model"),
            "generation_batch_id": rec.get("metadata", {}).get("generation_batch_id", ""),
            "metadata": rec.get("metadata", {}),
            "sets_detail": rec.get("sets_detail", [])
        } for rec in records]

    @classmethod
    def get_generation_session_by_id(cls, session_id: int):
        """Retrieves one generation session payload by session id."""
        try:
            sid = int(session_id)
        except Exception:
            return None
        if sid <= 0:
            return None
        sessions = cls.get_all_generation_history(max_sessions=1, session_ids=[sid])
        return sessions[0] if sessions else None

    @classmethod
    def get_generation_sessions_by_batch_id(cls, batch_id: str, max_sessions: int = None) -> list:
        """Retrieves all sessions for a specific generation batch id using indexed lookup."""
        normalized_batch_id = str(batch_id or "").strip()
        if not normalized_batch_id:
            return []

        if normalized_batch_id.startswith("session-"):
            try:
                sid = int(normalized_batch_id.replace("session-", ""))
            except Exception:
                return []
            session = cls.get_generation_session_by_id(sid)
            return [session] if isinstance(session, dict) else []

        limit_value = None
        if max_sessions is not None:
            try:
                parsed = int(max_sessions)
                if parsed > 0:
                    limit_value = parsed
            except Exception:
                limit_value = None

        cls._ensure_tables()
        db_path = cls._get_db_path()
        resolved_ids = []
        with cls._lock:
            conn = None
            try:
                conn = sqlite3.connect(db_path, timeout=30.0)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                query = "SELECT id FROM generation_sessions WHERE generation_batch_id = ? ORDER BY id DESC"
                params = [normalized_batch_id]
                if limit_value is not None:
                    query += " LIMIT ?"
                    params.append(limit_value)

                cursor.execute(query, tuple(params))
                rows = cursor.fetchall()
                for row in rows:
                    try:
                        sid = int(row["id"])
                    except Exception:
                        sid = 0
                    if sid > 0:
                        resolved_ids.append(sid)
            except Exception as e:
                _log.error(f"Failed to query sessions by batch id: {e}", exc_info=True)
                resolved_ids = []
            finally:
                if conn:
                    conn.close()

        if not resolved_ids:
            return []
        return cls.get_all_generation_history(session_ids=resolved_ids)

    @classmethod
    def get_generation_batch_history(cls, max_sessions: int = None) -> list:
        """Retrieves generation history grouped by generation_batch_id for history UX consumers."""
        sessions = cls.get_all_generation_history(max_sessions=max_sessions)
        grouped = {}

        for session in sessions:
            session_id = int(session.get("id", 0) or 0)
            raw_batch_id = str(session.get("generation_batch_id") or "").strip()
            batch_id = raw_batch_id or (f"session-{session_id}" if session_id > 0 else "session-unknown")

            metadata = session.get("metadata", {})
            if not isinstance(metadata, dict):
                metadata = {}

            timestamp = str(session.get("timestamp", "") or "")
            set_detail = session.get("sets_detail", [])
            set_count = len(set_detail) if isinstance(set_detail, list) else 0
            algorithm_title = str(
                session.get("algorithm_title")
                or metadata.get("algorithm_title")
                or "Statistical Distribution Model"
            )

            bucket = grouped.setdefault(batch_id, {
                "batch_id": batch_id,
                "is_fallback_batch": not bool(raw_batch_id),
                "session_ids": [],
                "session_count": 0,
                "set_count": 0,
                "algorithm_titles": [],
                "first_timestamp": "",
                "latest_timestamp": "",
                "has_top_ranked": False,
                "score_weight_profile": {},
            })

            if session_id and session_id not in bucket["session_ids"]:
                bucket["session_ids"].append(session_id)
                bucket["session_count"] += 1

            bucket["set_count"] += int(set_count)

            if algorithm_title and algorithm_title not in bucket["algorithm_titles"]:
                bucket["algorithm_titles"].append(algorithm_title)

            if timestamp:
                if not bucket["first_timestamp"] or timestamp < bucket["first_timestamp"]:
                    bucket["first_timestamp"] = timestamp
                if not bucket["latest_timestamp"] or timestamp > bucket["latest_timestamp"]:
                    bucket["latest_timestamp"] = timestamp

            top_ranked = metadata.get("top_ranked_combinations", [])
            if isinstance(top_ranked, list) and top_ranked:
                bucket["has_top_ranked"] = True

            profile = metadata.get("score_weight_profile", {})
            if (not bucket["score_weight_profile"]) and isinstance(profile, dict) and profile:
                bucket["score_weight_profile"] = profile

        results = list(grouped.values())
        results.sort(key=lambda item: (item.get("latest_timestamp", ""), item.get("batch_id", "")), reverse=True)
        return results

    @classmethod
    def optimize_bonus_swap(cls, generated_6_numbers: list, bonus_number: int, official_winning_numbers: list = None) -> dict:
        """Delegates bonus swap optimization simulation to LottoEvaluator."""
        winning_tuple = cls.get_latest_winning_numbers()
        if official_winning_numbers:
            winning_tuple = (set(official_winning_numbers), winning_tuple[1])
        return LottoEvaluator.optimize_bonus_swap(generated_6_numbers, bonus_number, winning_tuple)