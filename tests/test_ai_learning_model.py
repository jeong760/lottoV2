import os
import sys
import logging

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir) if "tests" in current_dir else current_dir
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ai import ai_learning_model


def test_known_torch_native_init_failure_logs_info(caplog):
    error = OSError(
        '[WinError 1114] DLL 초기화 루틴을 실행할 수 없습니다. Error loading "C:\\tmp\\torch\\lib\\c10.dll" or one of its dependencies.'
    )

    with caplog.at_level(logging.INFO, logger="AILearningModel"):
        ai_learning_model._log_torch_init_failure(error)

    message = "PyTorch could not be initialized"
    records = [record for record in caplog.records if message in record.getMessage()]
    assert records
    assert all(record.levelname == "INFO" for record in records)


def test_unknown_torch_init_failure_logs_warning(caplog):
    error = RuntimeError("unexpected torch bootstrap failure")

    with caplog.at_level(logging.INFO, logger="AILearningModel"):
        ai_learning_model._log_torch_init_failure(error)

    message = "PyTorch could not be initialized"
    records = [record for record in caplog.records if message in record.getMessage()]
    assert records
    assert all(record.levelname == "WARNING" for record in records)
