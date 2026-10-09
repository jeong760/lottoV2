import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir) if "tests" in current_dir else current_dir
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from data.repositories.lotto_repository import LottoRepository
from data.repositories.ml_model_repository import MLModelRepository


def _norm(path: str) -> str:
    return os.path.normcase(os.path.normpath(os.path.abspath(path)))


def test_lotto_repository_db_path_is_project_root_db():
    expected = _norm(os.path.join(project_root, "db", "lottomater.db"))
    actual = _norm(LottoRepository._get_db_path())
    assert actual == expected
    assert _norm(os.path.dirname(actual)) == _norm(os.path.join(project_root, "db"))


def test_ml_model_repository_db_path_is_project_root_db():
    expected = _norm(os.path.join(project_root, "db", "mllearn.db"))
    actual = _norm(MLModelRepository._get_db_path())
    assert actual == expected
    assert _norm(os.path.dirname(actual)) == _norm(os.path.join(project_root, "db"))


def test_ml_model_repository_path_fallback_stays_in_project_root(monkeypatch, tmp_path):
    expected = _norm(os.path.join(project_root, "db", "mllearn.db"))
    original_exists = os.path.exists
    resolution_error_raised = False

    def exists_with_recoverable_error(path):
        nonlocal resolution_error_raised
        if not resolution_error_raised:
            resolution_error_raised = True
            raise OSError("temporary path resolution error")
        return original_exists(path)

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        sys.modules[MLModelRepository.__module__].os.path,
        "exists",
        exists_with_recoverable_error,
    )

    actual = _norm(MLModelRepository._get_db_path())

    assert resolution_error_raised
    assert actual == expected
