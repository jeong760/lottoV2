# -*- coding: utf-8 -*-
# tests/test_quality_gate.py
import sys
import os
import logging
import pytest

# Ensure project root is in sys.path and initialize centralized logging
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir) if "tests" in current_dir else current_dir
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.logger import setup_logging
setup_logging(project_root)

_log = logging.getLogger("TestQualityGate")

from core.algorithm_hub import QualityGate
from config import SUM_MIN, SUM_MAX


def test_quality_gate_valid_combination():
    """Test whether a number combination meeting the passing criteria successfully passes (True)."""
    _log.info("Running test_quality_gate_valid_combination...")
    gate = QualityGate()
    # Sample numbers within the golden sum range, balanced odd/even ratio
    valid_nums = [5, 12, 19, 28, 34, 42] 
    
    is_passed, stats = gate.evaluate(valid_nums)
    _log.debug(f"Evaluation result: is_passed={is_passed}, stats={stats}")
    
    assert is_passed is True
    assert SUM_MIN <= stats["sum"] <= SUM_MAX
    assert 2 <= stats["odd_count"] <= 4
    assert stats["ac_value"] >= 4
    _log.info("test_quality_gate_valid_combination passed successfully.")


def test_quality_gate_invalid_sum():
    """Test combination that should fail (False) because the sum is below the minimum threshold."""
    _log.info("Running test_quality_gate_invalid_sum...")
    gate = QualityGate()
    invalid_nums = [1, 2, 3, 4, 5, 6]  # Sum is 21 (below SUM_MIN threshold)
    
    is_passed, stats = gate.evaluate(invalid_nums)
    _log.debug(f"Evaluation result: is_passed={is_passed}, stats={stats}")
    
    assert is_passed is False
    assert stats["sum"] < SUM_MIN
    _log.info("test_quality_gate_invalid_sum passed successfully.")