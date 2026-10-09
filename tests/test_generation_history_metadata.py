import os
import sys
import json
import sqlite3

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir) if "tests" in current_dir else current_dir
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from data.lotto_db_helper import LottoDBHelper


def test_generation_history_persists_session_metadata(monkeypatch, tmp_path):
    tmp_db_path = tmp_path / "phase_e_generation_history.db"
    monkeypatch.setattr(
        LottoDBHelper,
        "_get_db_path",
        staticmethod(lambda: str(tmp_db_path)),
    )

    metadata = {
        "algorithm_id": "ensemble_auto",
        "algorithm_title": "Advanced AI Ensemble",
        "confidence_score": 93.4,
        "score_weight_profile": {
            "probability": 0.34,
            "pattern": 0.21,
            "ai": 0.24,
            "genetic": 0.21,
            "confidence_probability": 0.43,
            "confidence_ensemble": 0.57,
        },
        "top_ranked_combinations": [
            {
                "rank": 1,
                "numbers": [3, 11, 17, 24, 35, 42],
                "confidence_score": 94.6,
                "probability_score": 91.2,
                "pattern_score": 88.7,
                "ai_score": 93.1,
                "genetic_score": 90.4,
                "ensemble_score": 92.2,
            }
        ],
    }
    generated_sets = [[3, 11, 17, 24, 35, 42, 7]]

    LottoDBHelper.save_generation_history(
        set_count=1,
        generated_sets=generated_sets,
        metadata=metadata,
    )

    sessions = LottoDBHelper.load_generation_history()
    assert sessions
    session_meta = sessions[0].get("metadata", {})
    assert isinstance(session_meta, dict)
    assert session_meta.get("algorithm_id") == "ensemble_auto"
    assert isinstance(session_meta.get("top_ranked_combinations"), list)
    assert session_meta["top_ranked_combinations"][0]["rank"] == 1

    flat = LottoDBHelper.get_generation_history()
    assert flat
    assert "session_metadata" in flat[0]
    assert "top_ranked_combinations" in flat[0]
    assert flat[0]["session_metadata"].get("algorithm_title") == "Advanced AI Ensemble"
    assert isinstance(flat[0]["score_weight_profile"], dict)

    all_history = LottoDBHelper.get_all_generation_history()
    assert all_history
    assert isinstance(all_history[0].get("metadata"), dict)
    assert all_history[0]["metadata"].get("algorithm_id") == "ensemble_auto"


def test_generation_history_backfills_rankings_with_batch_id(monkeypatch, tmp_path):
    tmp_db_path = tmp_path / "phase_f_generation_history.db"
    monkeypatch.setattr(
        LottoDBHelper,
        "_get_db_path",
        staticmethod(lambda: str(tmp_db_path)),
    )

    batch_id = "phase-f-batch-001"
    rich_metadata = {
        "algorithm_id": "ensemble_auto",
        "algorithm_title": "Phase F Ensemble",
        "generation_batch_id": batch_id,
        "score_weight_profile": {
            "probability": 0.33,
            "pattern": 0.22,
            "ai": 0.24,
            "genetic": 0.21,
        },
        "top_ranked_combinations": [
            {
                "rank": 1,
                "numbers": [1, 9, 13, 27, 31, 45],
                "confidence_score": 95.2,
                "probability_score": 92.5,
                "pattern_score": 89.4,
                "ai_score": 94.1,
                "genetic_score": 90.8,
                "ensemble_score": 93.3,
            }
        ],
    }
    lean_metadata = {
        "algorithm_id": "ensemble_auto",
        "algorithm_title": "Phase F Ensemble",
        "generation_batch_id": batch_id,
    }

    LottoDBHelper.save_generation_history(
        set_count=1,
        generated_sets=[[1, 9, 13, 27, 31, 45, 8]],
        metadata=rich_metadata,
    )
    LottoDBHelper.save_generation_history(
        set_count=1,
        generated_sets=[[2, 11, 18, 21, 33, 40, 7]],
        metadata=lean_metadata,
    )

    sessions = LottoDBHelper.load_generation_history()
    assert len(sessions) == 2
    for session in sessions:
        metadata = session.get("metadata", {})
        assert metadata.get("generation_batch_id") == batch_id
        assert isinstance(metadata.get("top_ranked_combinations"), list)
        assert metadata["top_ranked_combinations"][0]["rank"] == 1
        assert isinstance(metadata.get("score_weight_profile"), dict)
        assert metadata["score_weight_profile"]

    flat = LottoDBHelper.get_generation_history()
    assert len(flat) == 2
    for rec in flat:
        assert rec.get("top_ranked_combinations")
        assert rec["top_ranked_combinations"][0]["rank"] == 1


def test_generation_history_batch_id_column_fallback(monkeypatch, tmp_path):
    tmp_db_path = tmp_path / "phase_g_generation_history.db"
    monkeypatch.setattr(
        LottoDBHelper,
        "_get_db_path",
        staticmethod(lambda: str(tmp_db_path)),
    )

    LottoDBHelper._ensure_tables()
    batch_id = "phase-g-column-batch-001"

    conn = sqlite3.connect(str(tmp_db_path))
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO generation_sessions (created_at, set_count, algorithm_title, round_info, metadata_json, generation_batch_id)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            "2026-10-08 00:00:00",
            1,
            "Column Batch Algo",
            "Live Draw",
            json.dumps({"algorithm_title": "Column Batch Algo"}, ensure_ascii=False),
            batch_id,
        ),
    )
    session_id = cur.lastrowid
    cur.execute(
        """
        INSERT INTO generated_sets (
            session_id, created_at, round_info, set_no, algorithm_title,
            numbers, match_count, rounds_info, probability_str,
            num1, num2, num3, num4, num5, num6, bonus_no
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            session_id,
            "2026-10-08 00:00:00",
            "Live Draw",
            1,
            "Column Batch Algo",
            json.dumps([1, 3, 11, 17, 29, 42, 7], ensure_ascii=False),
            0,
            "-",
            "0.00%",
            1, 3, 11, 17, 29, 42, 7,
        ),
    )
    conn.commit()
    conn.close()

    sessions = LottoDBHelper.load_generation_history()
    assert sessions
    session_meta = sessions[0].get("metadata", {})
    assert session_meta.get("generation_batch_id") == batch_id

    all_history = LottoDBHelper.get_all_generation_history()
    assert all_history
    assert all_history[0].get("generation_batch_id") == batch_id


def test_generation_history_batch_id_legacy_metadata_backfill(monkeypatch, tmp_path):
    tmp_db_path = tmp_path / "phase_k_generation_history_legacy_backfill.db"
    monkeypatch.setattr(
        LottoDBHelper,
        "_get_db_path",
        staticmethod(lambda: str(tmp_db_path)),
    )

    conn = sqlite3.connect(str(tmp_db_path))
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE generation_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT,
            set_count INTEGER,
            algorithm_title TEXT,
            round_info TEXT DEFAULT 'Live Draw',
            metadata_json TEXT DEFAULT '{}'
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE generated_sets (
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
            bonus_no INTEGER
        )
        """
    )

    legacy_batch_id = "phase-k-legacy-batch-001"
    cur.execute(
        """
        INSERT INTO generation_sessions (created_at, set_count, algorithm_title, round_info, metadata_json)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            "2026-10-08 00:00:00",
            1,
            "Legacy Batch Algo",
            "Live Draw",
            json.dumps({
                "algorithm_title": "Legacy Batch Algo",
                "generation_batch_id": legacy_batch_id,
            }, ensure_ascii=False),
        ),
    )
    session_id = cur.lastrowid
    cur.execute(
        """
        INSERT INTO generated_sets (
            session_id, created_at, round_info, set_no, algorithm_title,
            numbers, match_count, rounds_info, probability_str,
            num1, num2, num3, num4, num5, num6, bonus_no
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            session_id,
            "2026-10-08 00:00:00",
            "Live Draw",
            1,
            "Legacy Batch Algo",
            json.dumps([3, 9, 14, 22, 35, 41, 7], ensure_ascii=False),
            0,
            "-",
            "0.00%",
            3, 9, 14, 22, 35, 41, 7,
        ),
    )
    conn.commit()
    conn.close()

    sessions = LottoDBHelper.get_generation_sessions_by_batch_id(legacy_batch_id)
    assert isinstance(sessions, list)
    assert len(sessions) == 1
    assert sessions[0].get("generation_batch_id") == legacy_batch_id
    assert sessions[0].get("algorithm_title") == "Legacy Batch Algo"


def test_generation_batch_history_groups_sessions(monkeypatch, tmp_path):
    tmp_db_path = tmp_path / "phase_h_generation_history.db"
    monkeypatch.setattr(
        LottoDBHelper,
        "_get_db_path",
        staticmethod(lambda: str(tmp_db_path)),
    )

    batch_id = "phase-h-batch-001"
    rich_metadata = {
        "algorithm_id": "ensemble_auto",
        "algorithm_title": "Phase H Ensemble",
        "generation_batch_id": batch_id,
        "score_weight_profile": {"probability": 0.31, "pattern": 0.22, "ai": 0.25, "genetic": 0.22},
        "top_ranked_combinations": [
            {"rank": 1, "numbers": [2, 8, 15, 24, 33, 41], "confidence_score": 94.1}
        ],
    }
    lean_metadata = {
        "algorithm_id": "ensemble_auto",
        "algorithm_title": "Phase H Ensemble",
        "generation_batch_id": batch_id,
    }
    fallback_metadata = {
        "algorithm_id": "single_session_mode",
        "algorithm_title": "Fallback Session",
    }

    LottoDBHelper.save_generation_history(
        set_count=1,
        generated_sets=[[2, 8, 15, 24, 33, 41, 9]],
        metadata=rich_metadata,
    )
    LottoDBHelper.save_generation_history(
        set_count=1,
        generated_sets=[[1, 10, 16, 25, 34, 42, 7]],
        metadata=lean_metadata,
    )
    LottoDBHelper.save_generation_history(
        set_count=1,
        generated_sets=[[3, 11, 17, 26, 35, 43, 6]],
        metadata=fallback_metadata,
    )

    grouped = LottoDBHelper.get_generation_batch_history()
    assert isinstance(grouped, list)
    assert grouped

    batch_row = next((row for row in grouped if row.get("batch_id") == batch_id), None)
    assert batch_row is not None
    assert batch_row.get("session_count") == 2
    assert batch_row.get("set_count") == 2
    assert batch_row.get("has_top_ranked") is True
    assert isinstance(batch_row.get("score_weight_profile"), dict)
    assert batch_row.get("score_weight_profile")
    assert isinstance(batch_row.get("session_ids"), list)
    assert len(batch_row.get("session_ids")) == 2

    fallback_row = next((row for row in grouped if str(row.get("batch_id", "")).startswith("session-")), None)
    assert fallback_row is not None
    assert fallback_row.get("is_fallback_batch") is True
    assert fallback_row.get("session_count") == 1


def test_generation_history_resilient_to_invalid_num_columns(monkeypatch, tmp_path):
    tmp_db_path = tmp_path / "phase_k_generation_history_invalid_nums.db"
    monkeypatch.setattr(
        LottoDBHelper,
        "_get_db_path",
        staticmethod(lambda: str(tmp_db_path)),
    )

    LottoDBHelper._ensure_tables()
    conn = sqlite3.connect(str(tmp_db_path))
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO generation_sessions (created_at, set_count, algorithm_title, round_info, metadata_json, generation_batch_id)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            "2026-10-08 00:00:00",
            1,
            "Invalid Num Columns",
            "Live Draw",
            json.dumps({"algorithm_title": "Invalid Num Columns"}, ensure_ascii=False),
            "phase-k-invalid-num",
        ),
    )
    session_id = cur.lastrowid
    cur.execute(
        """
        INSERT INTO generated_sets (
            session_id, created_at, round_info, set_no, algorithm_title,
            numbers, match_count, rounds_info, probability_str,
            num1, num2, num3, num4, num5, num6, bonus_no
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            session_id,
            "2026-10-08 00:00:00",
            "Live Draw",
            1,
            "Invalid Num Columns",
            json.dumps([4, 12, 18, 27, 33, 41, 8], ensure_ascii=False),
            0,
            "-",
            "0.00%",
            4, 12, "INVALID", 27, 33, 41, 8,
        ),
    )
    conn.commit()
    conn.close()

    loaded = LottoDBHelper.load_generation_history()
    assert loaded
    sets_detail = loaded[0].get("sets_detail", [])
    assert sets_detail
    nums = sets_detail[0].get("numbers", [])
    assert isinstance(nums, list)
    assert len(nums) == 6
    assert nums == [4, 12, 18, 27, 33, 41]


def test_generation_history_max_sessions_scope(monkeypatch, tmp_path):
    tmp_db_path = tmp_path / "phase_j_generation_history_limit.db"
    monkeypatch.setattr(
        LottoDBHelper,
        "_get_db_path",
        staticmethod(lambda: str(tmp_db_path)),
    )

    for idx in range(1, 4):
        LottoDBHelper.save_generation_history(
            set_count=1,
            generated_sets=[[idx, idx + 5, idx + 10, idx + 15, idx + 20, idx + 25, 7]],
            metadata={
                "algorithm_id": f"phase_j_{idx}",
                "algorithm_title": f"Phase J Algo {idx}",
                "generation_batch_id": f"phase-j-batch-{idx}",
            },
        )

    sessions_all = LottoDBHelper.load_generation_history()
    sessions_limited = LottoDBHelper.load_generation_history(max_sessions=2)

    assert len(sessions_all) == 3
    assert len(sessions_limited) == 2
    assert sessions_limited[0]["metadata"].get("algorithm_title") == "Phase J Algo 3"
    assert sessions_limited[1]["metadata"].get("algorithm_title") == "Phase J Algo 2"

    flat_limited = LottoDBHelper.get_generation_history(max_sessions=2)
    assert len(flat_limited) == 2
    assert flat_limited[0].get("algorithm_title") == "Phase J Algo 3"
    assert flat_limited[1].get("algorithm_title") == "Phase J Algo 2"


def test_generation_history_fast_lookup_helpers(monkeypatch, tmp_path):
    tmp_db_path = tmp_path / "phase_j_generation_history_lookup.db"
    monkeypatch.setattr(
        LottoDBHelper,
        "_get_db_path",
        staticmethod(lambda: str(tmp_db_path)),
    )

    batch_id = "phase-j-batch-lookup"
    LottoDBHelper.save_generation_history(
        set_count=1,
        generated_sets=[[4, 9, 14, 19, 24, 29, 1]],
        metadata={
            "algorithm_id": "phase_j_lookup_a",
            "algorithm_title": "Phase J Lookup A",
            "generation_batch_id": batch_id,
        },
    )
    LottoDBHelper.save_generation_history(
        set_count=1,
        generated_sets=[[5, 10, 15, 20, 25, 30, 2]],
        metadata={
            "algorithm_id": "phase_j_lookup_b",
            "algorithm_title": "Phase J Lookup B",
            "generation_batch_id": batch_id,
        },
    )
    LottoDBHelper.save_generation_history(
        set_count=1,
        generated_sets=[[6, 11, 16, 21, 26, 31, 3]],
        metadata={
            "algorithm_id": "phase_j_lookup_c",
            "algorithm_title": "Phase J Lookup C",
        },
    )

    all_history = LottoDBHelper.get_all_generation_history()
    title_to_id = {row.get("algorithm_title"): int(row.get("id", 0) or 0) for row in all_history}
    target_id = title_to_id.get("Phase J Lookup B", 0)
    assert target_id > 0

    single_session = LottoDBHelper.get_generation_session_by_id(target_id)
    assert isinstance(single_session, dict)
    assert single_session.get("id") == target_id
    assert single_session.get("algorithm_title") == "Phase J Lookup B"

    scoped_sessions = LottoDBHelper.load_generation_history(session_ids=[target_id])
    assert len(scoped_sessions) == 1
    assert scoped_sessions[0].get("session_id") == target_id

    by_batch = LottoDBHelper.get_generation_sessions_by_batch_id(batch_id)
    assert isinstance(by_batch, list)
    assert len(by_batch) == 2
    batch_titles = {row.get("algorithm_title") for row in by_batch}
    assert "Phase J Lookup A" in batch_titles
    assert "Phase J Lookup B" in batch_titles

    fallback_single = LottoDBHelper.get_generation_sessions_by_batch_id(f"session-{target_id}")
    assert len(fallback_single) == 1
    assert int(fallback_single[0].get("id", 0) or 0) == target_id


def test_save_generation_history_handles_metadata_json_encoder_edge_case(monkeypatch, tmp_path):
    tmp_db_path = tmp_path / "phase_l_generation_history_encoder_edge_case.db"
    monkeypatch.setattr(
        LottoDBHelper,
        "_get_db_path",
        staticmethod(lambda: str(tmp_db_path)),
    )

    original_dumps = json.dumps

    def flaky_dumps(obj, *args, **kwargs):
        if isinstance(obj, dict) and kwargs.get("default") is str and "indent" not in kwargs:
            raise TypeError("can't multiply sequence by non-int of type 'NoneType'")
        return original_dumps(obj, *args, **kwargs)

    monkeypatch.setattr("data.lotto_db_helper.json.dumps", flaky_dumps)

    LottoDBHelper.save_generation_history(
        set_count=1,
        generated_sets=[[7, 12, 18, 24, 36, 41, 5]],
        metadata={
            "algorithm_id": "encoder_edge_case",
            "algorithm_title": "Encoder Edge Case",
            "generation_batch_id": "phase-l-encoder-edge",
        },
    )

    sessions = LottoDBHelper.load_generation_history()
    assert len(sessions) == 1
    metadata = sessions[0].get("metadata", {})
    assert metadata.get("algorithm_title") == "Encoder Edge Case"
    assert metadata.get("generation_batch_id") == "phase-l-encoder-edge"
