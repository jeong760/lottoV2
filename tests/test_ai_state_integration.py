import os
import sys
import types

import numpy as np
import pytest


current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir) if "tests" in current_dir else current_dir
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.algorithms import group_ml_ai


if "PyQt5.QtCore" not in sys.modules:
    qtcore_stub = types.ModuleType("PyQt5.QtCore")

    class _QThread:
        def __init__(self, *args, **kwargs):
            pass

    def _pyqt_signal(*args, **kwargs):
        return object()

    qtcore_stub.QThread = _QThread
    qtcore_stub.pyqtSignal = _pyqt_signal

    pyqt_stub = types.ModuleType("PyQt5")
    pyqt_stub.QtCore = qtcore_stub

    sys.modules["PyQt5"] = pyqt_stub
    sys.modules["PyQt5.QtCore"] = qtcore_stub

from workers import lotto_worker


def _build_repository_state(boost_number: int) -> dict:
    neural = {str(i): 1.0 for i in range(1, 46)}
    balanced = {str(i): 1.0 for i in range(1, 46)}
    frequency = {str(i): 1.0 for i in range(1, 46)}
    neural[str(boost_number)] = 30.0
    balanced[str(boost_number)] = 20.0
    frequency[str(boost_number)] = 10.0
    return {
        "neural_weights": neural,
        "bias_analysis": {"balanced_weights": balanced},
        "frequency_distribution": frequency,
    }


def test_ai_smart_algorithm_uses_primary_repository_state(monkeypatch):
    calls = []
    captured = {}
    state = _build_repository_state(boost_number=45)

    def fake_load_model_state(key):
        calls.append(key)
        if key == "latest_weights_1_500":
            return state
        return None

    def fake_choice(candidate_pool, size, replace, p):
        captured["probs"] = np.asarray(p, dtype=np.float64)
        return np.array([45, 44, 43, 42, 41, 40], dtype=np.int64)

    monkeypatch.setattr(group_ml_ai.MLModelRepository, "load_model_state", staticmethod(fake_load_model_state))
    monkeypatch.setattr(group_ml_ai.os.path, "exists", lambda *_: False)
    monkeypatch.setattr(group_ml_ai.np.random, "choice", fake_choice)

    numbers = group_ml_ai.ai_smart_algorithm()

    assert calls == ["latest_weights_1_500"]
    assert numbers == [40, 41, 42, 43, 44, 45]
    assert pytest.approx(float(np.sum(captured["probs"])), rel=1e-9, abs=1e-9) == 1.0
    assert float(captured["probs"][44]) > float(captured["probs"][0])


def test_ai_smart_algorithm_falls_back_to_secondary_repository_key(monkeypatch):
    calls = []
    state = _build_repository_state(boost_number=33)
    captured = {}

    def fake_load_model_state(key):
        calls.append(key)
        if key == "latest_weights_1_500":
            return None
        if key == "latest_weights":
            return state
        return None

    def fake_choice(candidate_pool, size, replace, p):
        captured["probs"] = np.asarray(p, dtype=np.float64)
        return np.array([33, 1, 2, 3, 4, 5], dtype=np.int64)

    monkeypatch.setattr(group_ml_ai.MLModelRepository, "load_model_state", staticmethod(fake_load_model_state))
    monkeypatch.setattr(group_ml_ai.os.path, "exists", lambda *_: False)
    monkeypatch.setattr(group_ml_ai.np.random, "choice", fake_choice)

    numbers = group_ml_ai.ai_smart_algorithm()

    assert calls == ["latest_weights_1_500", "latest_weights"]
    assert numbers == [1, 2, 3, 4, 5, 33]
    assert float(captured["probs"][32]) > float(captured["probs"][0])


def test_lotto_worker_load_ai_weights_prefers_primary_repository_key(monkeypatch):
    calls = []
    primary_state = {"neural_weights": {"1": 1.2}}

    def fake_load_model_state(key):
        calls.append(key)
        if key == "latest_weights_1_500":
            return primary_state
        return None

    monkeypatch.setattr(lotto_worker.MLModelRepository, "load_model_state", staticmethod(fake_load_model_state))
    monkeypatch.setattr(lotto_worker.os.path, "exists", lambda *_: False)

    loaded = lotto_worker.LottoWorker._load_ai_weights(object())

    assert calls == ["latest_weights_1_500"]
    assert loaded == primary_state


def test_lotto_worker_load_ai_weights_falls_back_to_secondary_repository_key(monkeypatch):
    calls = []
    secondary_state = {"neural_weights": {"2": 1.3}}

    def fake_load_model_state(key):
        calls.append(key)
        if key == "latest_weights_1_500":
            return None
        if key == "latest_weights":
            return secondary_state
        return None

    monkeypatch.setattr(lotto_worker.MLModelRepository, "load_model_state", staticmethod(fake_load_model_state))
    monkeypatch.setattr(lotto_worker.os.path, "exists", lambda *_: False)

    loaded = lotto_worker.LottoWorker._load_ai_weights(object())

    assert calls == ["latest_weights_1_500", "latest_weights"]
    assert loaded == secondary_state
