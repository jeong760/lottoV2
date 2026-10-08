# -*- coding: utf-8 -*-
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
