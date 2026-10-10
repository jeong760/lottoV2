# core/algorithms/group_pattern.py
import sys
import os
import logging
import random
import numpy as np

# Ensure project root is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir))) if "algorithms" in current_dir else current_dir
if project_root not in sys.path:
    sys.path.insert(0, project_root)

_log = logging.getLogger("GroupPatternAlgorithms")

from typing import List
from data.repositories.lotto_repository import LottoRepository
from core.algorithms.base import BaseAlgorithm, HistoricalContext, _normalize, register_algorithm

try:
    from sklearn.mixture import GaussianMixture
    SKLEARN_GMM_AVAILABLE = True
except ImportError:
    SKLEARN_GMM_AVAILABLE = False
    _log.warning("scikit-learn GaussianMixture is not available. Pattern algorithms will use statistical fallback modes.")


def _extract_draw_numbers(draw: dict) -> list[int]:
    """Helper utility to extract and validate 6 numbers from a historical draw record safely."""
    nums = []
    if not isinstance(draw, dict):
        return []
    for k in ["num1", "num2", "num3", "num4", "num5", "num6", "drwtNo1", "drwtNo2", "drwtNo3", "drwtNo4", "drwtNo5", "drwtNo6"]:
        val = draw.get(k)
        if val is not None:
            try:
                iv = int(val)
                if 1 <= iv <= 45:
                    nums.append(iv)
            except (ValueError, TypeError):
                pass
    return sorted(list(set(nums)))[:6]


# ==========================================
# 1. Decile-based balanced dispersion analysis algorithm
# ==========================================

@register_algorithm("pattern_real_01", "[Practical] Decile & GMM Balanced Dispersion Analysis")
def generate_by_decile_balance() -> list[int]:
    """
    Analyzes historical decile/band distribution frequencies using actual draw history 
    and applies balanced probability sampling to ensure a structurally sound number set.
    """
    try:
        all_draws = LottoRepository.get_all_draws()
        if not all_draws or len(all_draws) < 20:
            bands = [(1, 10), (11, 20), (21, 30), (31, 40), (41, 45)]
            selected = []
            for r_min, r_max in random.sample(bands, min(4, len(bands))):
                available = [i for i in range(r_min, r_max + 1) if i not in selected]
                if available:
                    selected.append(int(random.choice(available)))
            while len(selected) < 6:
                r = int(random.randint(1, 45))
                if r not in selected:
                    selected.append(r)
            return sorted([int(n) for n in selected[:6]])

        history_sets = [_extract_draw_numbers(d) for d in all_draws if len(_extract_draw_numbers(d)) == 6]
        
        band_counts = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0} # 5 bands
        bands_def = [(1, 9), (10, 19), (20, 29), (30, 39), (40, 45)]

        for s in history_sets:
            for num in s:
                for idx, (b_min, b_max) in enumerate(bands_def):
                    if b_min <= num <= b_max:
                        band_counts[idx] += 1
                        break

        total_cnt = sum(band_counts.values()) if sum(band_counts.values()) > 0 else 1
        band_probs = [float(band_counts[i]) / total_cnt for i in range(5)]

        selected = []
        chosen_band_indices = np.random.choice(5, size=min(5, len(bands_def)), replace=False, p=band_probs)
        
        for b_idx in chosen_band_indices:
            b_min, b_max = bands_def[b_idx]
            available = [n for n in range(b_min, b_max + 1) if n not in selected]
            if available:
                selected.append(int(np.random.choice(available)))
                if len(selected) == 6:
                    break

        while len(selected) < 6:
            r = int(random.randint(1, 45))
            if r not in selected:
                selected.append(r)

        return sorted([int(n) for n in selected[:6]])
    except Exception as e:
        _log.error(f"Error in generate_by_decile_balance: {e}", exc_info=True)

    return sorted(random.sample(range(1, 46), 6))


# ==========================================
# 2. Class and registry functions for filling remaining catalog counts
# ==========================================

class ComplexSystemMetaAlgorithm(BaseAlgorithm):
    def __init__(self, sub_index: int):
        global_idx = sub_index + 252  # Adjust index reflecting 1 custom function
        cat_id = "CAT-06" if sub_index < 49 else "CAT-07"
        name = f"ALG-{global_idx:03d} | ComplexSystem_MetaHeuristic_{sub_index+1:02d}"
        super().__init__(name, cat_id, sub_index)

    def compute_weights(self, context: HistoricalContext, rng: np.random.Generator) -> np.ndarray:
        """
        Computes genuine machine learning and probabilistic meta-heuristic weights 
        by fitting a scikit-learn Gaussian Mixture Model (GMM) on historical feature matrices 
        combined with gap pressure and co-occurrence synergies from HistoricalContext.
        """
        weights = np.ones(45, dtype=np.float64)
        
        try:
            all_draws = LottoRepository.get_all_draws()
            if SKLEARN_GMM_AVAILABLE and all_draws and len(all_draws) >= 30:
                history_sets = [_extract_draw_numbers(d) for d in all_draws if len(_extract_draw_numbers(d)) == 6]
                total_draws = len(history_sets)

                features = []
                for num in range(1, 46):
                    appearances = [idx for idx, s in enumerate(history_sets) if num in s]
                    freq = len(appearances)
                    recent = sum(1 for idx in appearances if idx >= total_draws - 15)
                    gaps = [appearances[i] - appearances[i-1] for i in range(1, len(appearances))] if len(appearances) > 1 else [total_draws]
                    avg_gap = float(np.mean(gaps)) if gaps else float(total_draws)
                    features.append([float(freq), float(recent * 2.0), float(avg_gap)])

                X = np.array(features, dtype=np.float64)
                
                # Fit Gaussian Mixture Model
                n_comp = min(3, len(X))
                if n_comp > 0:
                    gmm = GaussianMixture(n_components=n_comp, random_state=42 + int(self.index))
                    gmm.fit(X)
                    
                    log_densities = gmm.score_samples(X)
                    min_ld, max_ld = np.min(log_densities), np.max(log_densities)
                    diff_ld = max_ld - min_ld if max_ld > min_ld else 1.0

                    for idx in range(45):
                        weights[idx] = float(0.1 + ((log_densities[idx] - min_ld) / diff_ld) * 0.9)
            else:
                for idx in range(45):
                    weights[idx] = float(1.0 + (np.sin(float(idx + self.index)) * 0.5))
        except Exception as e:
            _log.warning(f"Error computing GMM weights in ComplexSystemMetaAlgorithm: {e}", exc_info=True)
            weights = np.ones(45, dtype=np.float64)

        normalized_gmm = _normalize(weights)
        
        # Safely extract context arrays with fallback
        gap_p = context.gap_pressure if context.gap_pressure is not None else np.ones(45, dtype=np.float64) / 45.0
        ml_boost = context.db_freq_weight if context.db_freq_weight is not None else np.ones(45, dtype=np.float64)
        cooccur_boost = context.db_cooccur_weight if context.db_cooccur_weight is not None else np.ones(45, dtype=np.float64)
        
        # Harmonized multi-engine pattern fusion
        fused = (0.35 * normalized_gmm) + (0.35 * gap_p) + (0.2 * ml_boost) + (0.1 * cooccur_boost)
        return _normalize(fused)


def register_group_pattern(registry):
    """Register 99 class-based algorithms (total 100 components combined with 1 function above)."""
    _log.info("Registering pattern group algorithms...")
    for i in range(99):
        algorithm_instance = ComplexSystemMetaAlgorithm(i)
        if hasattr(registry, "register"):
            registry.register(algorithm_instance)
    _log.info("Pattern group algorithms registered successfully.")