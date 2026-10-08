# -*- coding: utf-8 -*-
import os
import sys

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
