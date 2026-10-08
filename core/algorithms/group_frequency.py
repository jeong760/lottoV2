# -*- coding: utf-8 -*-
# core/algorithms/group_frequency.py
sys = __import__('sys')
os = __import__('os')
import logging
import random
import numpy as np

# Ensure project root is in sys.path and initialize centralized logging
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir))) if "algorithms" in current_dir else current_dir
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.logger import setup_logging
setup_logging(project_root)

_log = logging.getLogger("GroupFrequencyAlgorithms")

from typing import List, Dict, Any
from data.repositories.lotto_repository import LottoRepository
from core.algorithms.base import BaseAlgorithm, HistoricalContext, _normalize, register_algorithm


def _extract_draw_numbers(draw: dict) -> List[int]:
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
# 1. Balanced practical hybrid functional algorithm
# ==========================================

@register_algorithm("freq_balanced_01", "[Balanced Practical] Bias-Preventing Weighted Dispersion Hybrid")
def generate_balanced_hybrid() -> List[int]:
    """
    Smoothly adjusts weights to prevent specific number clustering and performs 
    probabilistic band-based sampling to ensure even dispersion across all 45 numbers, 
    integrated with historical repository frequencies and recent draw penalties.
    """
    try:
        all_draws = LottoRepository.get_all_draws()
        history_sets = [_extract_draw_numbers(d) for d in all_draws if len(_extract_draw_numbers(d)) == 6] if all_draws else []
        
        if not history_sets:
            return sorted(random.sample(range(1, 46), 6))
        
        weights = {i: 1.0 for i in range(1, 46)}
        freq_map = {i: 0 for i in range(1, 46)}
        
        for s in history_sets:
            for num in s:
                if 1 <= num <= 45:
                    freq_map[num] += 1
                
        max_freq = max(freq_map.values()) if freq_map else 1
        if max_freq > 0:
            for num, cnt in freq_map.items():
                weights[num] += (float(cnt) / float(max_freq)) * 1.5

        recent_draws = history_sets[-5:] if len(history_sets) >= 5 else history_sets
        for s in recent_draws:
            for num in s:
                if 1 <= num <= 45 and num in weights:
                    weights[num] *= 0.6 

        # Standardized Lottomaster bands (1-10, 11-20, 21-30, 31-40, 41-45)
        ranges = [
            list(range(1, 11)),
            list(range(11, 21)),
            list(range(21, 31)),
            list(range(31, 41)),
            list(range(41, 46))
        ]
        
        selected = []
        for r_pool in ranges:
            pool_weights = [max(0.01, float(weights[n])) for n in r_pool]
            total_pw = sum(pool_weights)
            if total_pw > 0:
                probs = np.array(pool_weights, dtype=np.float64)
                probs /= probs.sum()
                chosen = np.random.choice(r_pool, p=probs)
            else:
                chosen = random.choice(r_pool)
            selected.append(int(chosen))
            
        population = list(weights.keys())
        weight_values = [max(0.01, float(weights[i])) for i in population]
        
        attempts = 0
        while len(selected) < 6 and attempts < 100:
            attempts += 1
            total_w = sum(weight_values)
            if total_w > 0:
                probs = np.array(weight_values, dtype=np.float64)
                probs /= probs.sum()
                extra = int(np.random.choice(population, p=probs))
            else:
                extra = random.choice(population)
                
            if extra not in selected:
                selected.append(extra)
            
        while len(selected) < 6:
            extra = int(random.randint(1, 45))
            if extra not in selected:
                selected.append(extra)
                
        return sorted([int(n) for n in selected[:6]])
    except Exception as e:
        _log.error(f"Error in generate_balanced_hybrid: {e}", exc_info=True)
        return sorted(random.sample(range(1, 46), 6))


# ==========================================
# 2. Class-based remaining frequency group algorithms and registry functions
# ==========================================

class ProbabilisticConstraintAlgorithm(BaseAlgorithm):
    def __init__(self, sub_index: int):
        global_idx = sub_index + 52
        name = f"ALG-{global_idx:03d} | Prob_Constraint_Model_{sub_index+1:02d}"
        super().__init__(name, "CAT-02", sub_index)

    def compute_weights(self, context: HistoricalContext, rng: np.random.Generator) -> np.ndarray:
        """
        Computes robust weights combining transition probabilities, rarity ratios, parity preferences, 
        machine learning frequency propensities, and co-occurrence matrix synergies from HistoricalContext.
        """
        trans = context.transition_strength if context.transition_strength is not None else np.ones(45, dtype=np.float64) / 45.0
        freq_v = context.freq if context.freq is not None else np.ones(45, dtype=np.float64) / 45.0
        parity_pref = context.parity_preference if context.parity_preference is not None else np.ones(45, dtype=np.float64) / 45.0
        low_high_pref = context.low_high_preference if context.low_high_preference is not None else np.ones(45, dtype=np.float64) / 45.0

        transition = trans * 0.25
        rarity = _normalize(1.0 / (freq_v + 0.01)) * 0.25
        parity = _normalize(parity_pref * low_high_pref) * 0.20
        
        # [Ensemble Synergy Integration] Incorporate DB frequency propensities and co-occurrence weights from context
        ml_boost = context.db_freq_weight if context.db_freq_weight is not None else np.ones(45, dtype=np.float64)
        cooccur_boost = context.db_cooccur_weight if context.db_cooccur_weight is not None else np.ones(45, dtype=np.float64)
        
        fused = transition + rarity + parity + (0.20 * ml_boost) + (0.10 * cooccur_boost)
        return _normalize(fused)


def register_group_frequency(registry):
    """Batch registers frequency group algorithms into the registry."""
    _log.info("Registering frequency group algorithms...")
    for i in range(49):
        algorithm_instance = ProbabilisticConstraintAlgorithm(i)
        if hasattr(registry, "register"):
            registry.register(algorithm_instance)
    _log.info("Frequency group algorithms registered successfully.")