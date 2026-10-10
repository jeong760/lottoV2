# core/engines/monte_carlo_validator.py
import logging
import random
import numpy as np
from typing import List, Dict, Any

_log = logging.getLogger("MonteCarloValidator")


class MonteCarloValidator:
    """
    Performs Monte Carlo simulations to validate the statistical integrity, 
    sum distribution, and feature likelihood of generated lotto candidate sets.
    """

    def __init__(self, historical_draws: list[list[int]] = None):
        _log.info("Initializing MonteCarloValidator...")
        self.historical_draws = historical_draws or []
        self.mean_sum = 138.5
        self.std_sum = 15.0
        if self.historical_draws:
            self._recalculate_baseline()

    def update_history(self, historical_draws: list[list[int]]):
        """Updates internal history and recalculates baseline statistical parameters safely."""
        self.historical_draws = historical_draws or []
        self._recalculate_baseline()

    def _recalculate_baseline(self):
        """Calculates baseline sum mean and standard deviation from historical draws."""
        try:
            sums = []
            for draw in self.historical_draws:
                valid = []
                for n in draw:
                    try:
                        iv = int(n)
                        if 1 <= iv <= 45:
                            valid.append(iv)
                    except (ValueError, TypeError):
                        pass
                if len(valid) >= 6:
                    sums.append(sum(valid[:6]))
            if sums:
                self.mean_sum = float(np.mean(sums))
                self.std_sum = float(np.std(sums)) or 15.0
        except Exception as e:
            _log.warning(f"Error recalculating baseline in MonteCarloValidator: {e}", exc_info=True)

    def evaluate_set_probability(self, candidate_set: list[int]) -> dict[str, Any]:
        """
        Evaluates a candidate 6-number set using Monte Carlo probability scoring.
        Returns a dictionary containing validity flag and confidence score.
        """
        try:
            if not isinstance(candidate_set, list) or len(candidate_set) != 6:
                return {"is_valid": False, "confidence": 0.0}

            valid_cand = []
            for n in candidate_set:
                try:
                    iv = int(n)
                    if 1 <= iv <= 45:
                        valid_cand.append(iv)
                except (ValueError, TypeError):
                    pass

            if len(valid_cand) != 6:
                return {"is_valid": False, "confidence": 0.0}

            cand_sum = sum(valid_cand)
            sum_z_score = float(abs(cand_sum - self.mean_sum) / self.std_sum)

            # Confidence based on normal distribution proximity to historical sum mean
            base_confidence = float(max(60.0, 100.0 - (sum_z_score * 12.0)))
            
            matches = 0
            cand_set = set(valid_cand)
            
            # Check overlap tendency and structural health against historical samples
            if self.historical_draws:
                sample_history = random.sample(self.historical_draws, min(len(self.historical_draws), 100))
                for hist in sample_history:
                    hist_valid = {int(n) for n in hist if n is not None and str(n).isdigit() and 1 <= int(n) <= 45}
                    overlap = len(cand_set.intersection(hist_valid))
                    if overlap <= 2:
                        matches += 1
                overlap_ratio = float(matches) / float(len(sample_history)) if sample_history else 0.5
                confidence = round(float(base_confidence * (0.8 + 0.2 * overlap_ratio)), 2)
            else:
                confidence = round(float(base_confidence), 2)

            confidence = float(max(50.0, min(99.9, confidence)))
            is_valid = bool(sum_z_score <= 2.5)  # Must be within 2.5 standard deviations

            return {
                "is_valid": is_valid,
                "confidence": confidence,
                "sum_z_score": round(sum_z_score, 2)
            }
        except Exception as e:
            _log.warning(f"Error in MonteCarloValidator evaluation: {e}", exc_info=True)
            return {"is_valid": False, "confidence": 0.0, "sum_z_score": 0.0}