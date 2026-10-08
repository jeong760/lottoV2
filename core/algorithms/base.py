# -*- coding: utf-8 -*-
# core/algorithms/base.py
from __future__ import annotations
import sys
import os
import logging
import hashlib
import random
import numpy as np  # Explicitly declared so 'np' is available across all algorithm modules

# Ensure project root is in sys.path and initialize centralized logging
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir))) if "algorithms" in current_dir else current_dir
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.logger import setup_logging
setup_logging(project_root)

_log = logging.getLogger("AlgorithmBase")

from dataclasses import dataclass
from typing import List, Sequence, Dict, Tuple, Optional, Callable, Any, Union

NUMBERS = np.arange(1, 46, dtype=float)
EPSILON = 1e-9

# ==========================================
# Algorithm registration decorator and global registry
# ==========================================
FUNCTION_ALGORITHM_REGISTRY: Dict[str, Dict[str, Any]] = {}


def register_algorithm(algorithm_id: str, title: str):
    """Decorator to register function-based algorithms (such as real ML engines)."""
    def decorator(func: Callable):
        FUNCTION_ALGORITHM_REGISTRY[algorithm_id] = {
            "title": title,
            "func": func
        }
        _log.debug(f"Registered algorithm '{algorithm_id}' ({title})")
        return func
    return decorator


def _normalize(values: Sequence[float]) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    array = np.nan_to_num(array, nan=0.0, posinf=0.0, neginf=0.0)
    array = np.abs(array)
    total = float(np.sum(array))
    if total <= EPSILON:
        n = array.size if array.size > 0 else 45
        return np.full(n, 1.0 / float(n), dtype=float)
    return array / total


def _stable_seed(signature: str, algorithm_name: str, salt: str = "") -> int:
    payload = f"{signature}|{algorithm_name}|{salt}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big", signed=False)


def _weighted_pick(weights: np.ndarray, rng: np.random.Generator) -> List[int]:
    probabilities = _normalize(weights)
    if probabilities.size != 45:
        aligned = np.full(45, EPSILON, dtype=float)
        usable = min(probabilities.size, 45)
        if usable > 0:
            aligned[:usable] = np.maximum(probabilities[:usable], EPSILON)
        probabilities = _normalize(aligned)
    
    # Ensure exact probability sum of 1.0 for np.random.Generator.choice
    prob_sum = float(np.sum(probabilities))
    if prob_sum > 0:
        probabilities = probabilities / prob_sum
    else:
        probabilities = np.full(45, 1.0 / 45.0, dtype=float)

    picked = rng.choice(np.arange(1, 46), size=6, replace=False, p=probabilities)
    return sorted(int(number) for number in picked)


def _calculate_ac_value(numbers: Sequence[int]) -> int:
    """Calculates Arithmetic Complexity (AC value) for a number set."""
    try:
        diffs = set()
        valid = [int(n) for n in numbers if 1 <= int(n) <= 45]
        n = len(valid)
        for i in range(n):
            for j in range(i + 1, n):
                diffs.add(abs(valid[i] - valid[j]))
        return max(0, len(diffs) - (n - 1))
    except Exception:
        return 7


@dataclass(frozen=True)
class AlgorithmOutcome:
    name: str
    category: str
    numbers: List[int]
    weights: np.ndarray
    confidence: float


@dataclass(frozen=True)
class HistoricalContext:
    draws: np.ndarray
    draw_count: int
    freq: np.ndarray
    recent_freq: np.ndarray
    medium_freq: np.ndarray
    recency: np.ndarray
    hotness: np.ndarray
    gap_pressure: np.ndarray
    pair_centrality: np.ndarray
    transition_strength: np.ndarray
    position_bias: np.ndarray
    entropy_profile: np.ndarray
    momentum: np.ndarray
    parity_preference: np.ndarray
    low_high_preference: np.ndarray
    sum_mean: float
    sum_std: float
    odd_mean: float
    low_mean: float
    range_mean: float
    spread_mean: float
    ac_mean: float
    ac_std: float
    signature: str
    db_freq_weight: Optional[np.ndarray] = None
    db_cooccur_weight: Optional[np.ndarray] = None

    @classmethod
    def build(
        cls, 
        historical_draws: Optional[Sequence[Sequence[int]]] = None, 
        ml_weights: Optional[np.ndarray] = None,
        cooccur_weights: Optional[np.ndarray] = None
    ) -> "HistoricalContext":
        """Builds historical context tensors and computes real statistical, entropy, and complexity metrics from draws."""
        cleaned = []
        for draw in historical_draws or []:
            try:
                unique = sorted({int(n) for n in draw if str(n).isdigit() and 1 <= int(n) <= 45})
                if len(unique) >= 6:
                    cleaned.append(unique[:6])
            except Exception:
                continue

        if not cleaned:
            uniform = np.full(45, 1.0 / 45.0, dtype=float)
            neutral = np.zeros(45, dtype=float)
            return cls(
                draws=np.empty((0, 6), dtype=int), draw_count=0,
                freq=uniform, recent_freq=uniform, medium_freq=uniform,
                recency=uniform, hotness=neutral, gap_pressure=uniform,
                pair_centrality=uniform, transition_strength=uniform,
                position_bias=uniform, entropy_profile=uniform, momentum=neutral,
                parity_preference=uniform, low_high_preference=uniform,
                sum_mean=0.0, sum_std=1.0, odd_mean=3.0, low_mean=3.0,
                range_mean=35.0, spread_mean=7.0, ac_mean=7.0, ac_std=1.0,
                signature=hashlib.sha256(b"").hexdigest(),
                db_freq_weight=ml_weights if ml_weights is not None else np.ones(45, dtype=float),
                db_cooccur_weight=cooccur_weights if cooccur_weights is not None else np.ones(45, dtype=float)
            )

        draws = np.array(cleaned, dtype=int)
        draw_count = int(draws.shape[0])
        
        # Frequency and window analyses
        freq_counts = np.bincount(draws.ravel(), minlength=46)[1:].astype(float)
        freq = _normalize(freq_counts)
        
        recent_window = draws[-min(draw_count, 20):]
        medium_window = draws[-min(draw_count, 60):]
        recent_freq = _normalize(np.bincount(recent_window.ravel(), minlength=46)[1:].astype(float))
        medium_freq = _normalize(np.bincount(medium_window.ravel(), minlength=46)[1:].astype(float))
        hotness = np.clip((recent_freq - freq) + (recent_freq - medium_freq), -1.0, 1.0)
        
        # Recency & Gap pressure
        last_seen = np.full(45, draw_count + 1, dtype=float)
        for idx, draw in enumerate(draws):
            for n in draw:
                if 1 <= n <= 45:
                    last_seen[n - 1] = draw_count - idx
        recency = _normalize(1.0 / (last_seen + 0.75))
        
        # Pair centrality and transition matrix
        pair_counts = np.zeros((45, 45), dtype=float)
        for draw in draws:
            for l, r in zip(draw[:-1], draw[1:]):
                if 1 <= l <= 45 and 1 <= r <= 45:
                    pair_counts[l-1, r-1] += 1.0
        pair_centrality = _normalize(pair_counts.sum(axis=1) + 1.0)
        transition_strength = _normalize(pair_centrality + freq)
        position_bias = _normalize(np.bincount(draws.ravel(), minlength=46)[1:].astype(float))
        
        # Real Shannon Entropy profile calculation for each number across historical draws
        p_appear = freq_counts / float(draw_count)
        p_safe = np.clip(p_appear, 1e-10, 1.0 - 1e-10)
        shannon_entropy = -p_safe * np.log2(p_safe) - (1.0 - p_safe) * np.log2(1.0 - p_safe)
        entropy_profile = _normalize(shannon_entropy)
        
        momentum = _normalize(recent_freq)
        parity_preference = _normalize(np.array([1.2 if i % 2 else 0.8 for i in range(1, 46)]))
        low_high_preference = _normalize(np.array([1.2 if i <= 22 else 0.8 for i in range(1, 46)]))
        
        # Automatic co-occurrence propensity array derivation
        default_cooccur = _normalize(pair_counts.sum(axis=0) + pair_counts.sum(axis=1) + 1.0)
        
        # Real structural feature metrics extracted from draws
        sums = np.sum(draws, axis=1).astype(float)
        odd_counts = [sum(1 for n in draw if n % 2 != 0) for draw in draws]
        low_counts = [sum(1 for n in draw if 1 <= n <= 22) for draw in draws]
        ranges = [int(np.max(draw) - np.min(draw)) for draw in draws]
        spreads = [float(np.mean(np.diff(draw))) for draw in draws]
        ac_values = [_calculate_ac_value(draw) for draw in draws]

        return cls(
            draws=draws, draw_count=draw_count, freq=freq, recent_freq=recent_freq,
            medium_freq=medium_freq, recency=recency, hotness=hotness,
            gap_pressure=recency, pair_centrality=pair_centrality,
            transition_strength=transition_strength, position_bias=position_bias,
            entropy_profile=entropy_profile, momentum=momentum,
            parity_preference=parity_preference, low_high_preference=low_high_preference,
            sum_mean=float(np.mean(sums)), sum_std=float(np.std(sums) + 1.0),
            odd_mean=float(np.mean(odd_counts)), low_mean=float(np.mean(low_counts)),
            range_mean=float(np.mean(ranges)), spread_mean=float(np.mean(spreads)),
            ac_mean=float(np.mean(ac_values)), ac_std=float(np.std(ac_values) + 1.0),
            signature=hashlib.sha256(draws.tobytes()).hexdigest(),
            db_freq_weight=ml_weights if ml_weights is not None else _normalize(freq_counts + 1.0),
            db_cooccur_weight=cooccur_weights if cooccur_weights is not None else default_cooccur
        )


class BaseAlgorithm:
    def __init__(self, name: str, category: str, index: int):
        self.name = name
        self.category = category
        self.index = index

    def generate(self, context: HistoricalContext) -> AlgorithmOutcome:
        rng = np.random.default_rng(_stable_seed(context.signature, self.name, self.category))
        weights = _normalize(self.compute_weights(context, rng))
        numbers = _weighted_pick(weights, rng)
        top_mass = float(np.sum(np.sort(weights)[-6:]))
        confidence = min(1.0, max(0.0, top_mass * 2.4))
        return AlgorithmOutcome(self.name, self.category, numbers, weights, confidence)

    def compute_weights(self, context: HistoricalContext, rng: np.random.Generator) -> np.ndarray:
        raise NotImplementedError