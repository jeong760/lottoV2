# core/engines/markov_transition_engine.py
import logging
import numpy as np
from typing import List, Dict, Any, Optional

_log = logging.getLogger("MarkovTransitionEngine")


class MarkovTransitionEngine:
    """
    Computes transition probabilities between consecutive lotto draws using 
    Markov Chain modeling to bias number generation toward historically probable state shifts.
    """

    def __init__(self, historical_draws: list[list[int]] = None):
        _log.info("Initializing MarkovTransitionEngine...")
        self.historical_draws = historical_draws or []
        self.transition_matrix = np.zeros((46, 46), dtype=np.float64)
        if self.historical_draws:
            self._build_transition_matrix()

    def update_history(self, historical_draws: list[list[int]]):
        """Updates internal historical draws and rebuilds the transition matrix safely."""
        self.historical_draws = historical_draws or []
        self._build_transition_matrix()

    def _build_transition_matrix(self):
        """Builds a 46x46 Markov transition probability matrix from draw t to draw t+1 with Laplace smoothing."""
        try:
            self.transition_matrix = np.ones((46, 46), dtype=np.float64) * 0.01
            if len(self.historical_draws) < 2:
                return

            for i in range(len(self.historical_draws) - 1):
                curr_draw = self.historical_draws[i]
                next_draw = self.historical_draws[i+1]
                
                curr_valid = []
                for u in curr_draw:
                    try:
                        iv = int(u)
                        if 1 <= iv <= 45:
                            curr_valid.append(iv)
                    except (ValueError, TypeError):
                        pass

                next_valid = []
                for v in next_draw:
                    try:
                        iv = int(v)
                        if 1 <= iv <= 45:
                            next_valid.append(iv)
                    except (ValueError, TypeError):
                        pass

                for u in curr_valid:
                    for v in next_valid:
                        self.transition_matrix[u][v] += 1.0

            # Normalize rows to form valid probability distributions
            row_sums = self.transition_matrix.sum(axis=1, keepdims=True)
            row_sums[row_sums == 0] = 1.0
            self.transition_matrix = self.transition_matrix / row_sums
            _log.info("Markov transition matrix successfully built and normalized.")
        except Exception as e:
            _log.error(f"Error building Markov transition matrix: {e}", exc_info=True)

    def sample_markov_biased_numbers(self, count: int, reference_draw: list[int] = None) -> list[int]:
        """Samples numbers based on transition probabilities from a reference draw with safety guards."""
        try:
            if not reference_draw and self.historical_draws:
                reference_draw = self.historical_draws[-1]
            if not reference_draw:
                return sorted(np.random.choice(range(1, 46), size=min(int(count), 45), replace=False).tolist())

            probs = np.zeros(46, dtype=np.float64)
            for u in reference_draw:
                try:
                    iu = int(u)
                    if 1 <= iu <= 45:
                        probs += self.transition_matrix[iu]
                except (ValueError, TypeError):
                    pass

            probs[0] = 0.0
            total = probs.sum()
            if total > 0:
                probs = probs / total
            else:
                probs[1:] = 1.0 / 45.0

            candidate_pool = list(range(1, 46))
            sampled = np.random.choice(candidate_pool, size=min(int(count), 45), replace=False, p=probs[1:])
            return sorted([int(n) for n in sampled])
        except Exception as e:
            _log.warning(f"Error during Markov biased sampling, falling back to random: {e}", exc_info=True)
            return sorted(np.random.choice(range(1, 46), size=min(int(count), 45), replace=False).tolist())