import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir) if "tests" in current_dir else current_dir
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.algorithm_hub import AlgorithmHub


def _build_hub_without_init() -> AlgorithmHub:
    hub = AlgorithmHub.__new__(AlgorithmHub)
    hub.engine = None
    return hub


def test_apply_filters_rejects_duplicate_number_sets(monkeypatch):
    hub = _build_hub_without_init()
    monkeypatch.setattr(hub, "_get_latest_draw_numbers", lambda: [])

    candidates = [
        [1, 1, 12, 23, 34, 45],   # duplicate number -> must be rejected
        [2, 7, 14, 23, 31, 45],   # valid
    ]

    filtered = hub._apply_independence_and_overlap_filters(candidates, fixed_numbers=[], excluded_numbers=[])

    assert [2, 7, 14, 23, 31, 45] in filtered
    assert all(len(set(row)) == 6 for row in filtered)


def test_generate_premium_numbers_fallback_honors_fixed_and_excluded_constraints(monkeypatch):
    hub = _build_hub_without_init()

    monkeypatch.setattr(hub, "_get_dynamic_algorithm_weights", lambda: {})
    monkeypatch.setattr(hub, "generate_prediction_sets", lambda **kwargs: [])
    monkeypatch.setattr(hub, "_apply_independence_and_overlap_filters", lambda sets, *_: [])
    monkeypatch.setattr(hub, "_evolve_candidate_sets", lambda *args, **kwargs: [])
    monkeypatch.setattr(hub, "_diversify_sets_with_kmeans", lambda *args, **kwargs: [])
    monkeypatch.setattr(hub, "_score_candidate_set", lambda _: 90.0)

    generated_sets, _, _, _ = hub.generate_premium_numbers(
        set_count=3,
        fixed_numbers=[1, 2],
        excluded_numbers=[3, 4, 5],
        selected_algorithm_id="ensemble_auto",
    )

    assert len(generated_sets) == 3
    for row in generated_sets:
        assert {1, 2}.issubset(set(row))
        assert 3 not in row and 4 not in row and 5 not in row


def test_generate_premium_numbers_exception_fallback_honors_constraints(monkeypatch):
    hub = _build_hub_without_init()

    monkeypatch.setattr(hub, "_get_dynamic_algorithm_weights", lambda: {})
    monkeypatch.setattr(hub, "generate_prediction_sets", lambda **kwargs: [])
    monkeypatch.setattr(hub, "_apply_independence_and_overlap_filters", lambda sets, *_: [])
    monkeypatch.setattr(hub, "_evolve_candidate_sets", lambda *args, **kwargs: [])
    monkeypatch.setattr(hub, "_diversify_sets_with_kmeans", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("force fallback")))

    generated_sets, _, _, metadata = hub.generate_premium_numbers(
        set_count=2,
        fixed_numbers=[6],
        excluded_numbers=[7, 8, 9],
        selected_algorithm_id="ensemble_auto",
    )

    assert metadata.get("algorithm_title") == "Fallback Engine"
    assert len(generated_sets) == 2
    for row in generated_sets:
        assert 6 in row
        assert 7 not in row and 8 not in row and 9 not in row
