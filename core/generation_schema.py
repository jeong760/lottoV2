# -*- coding: utf-8 -*-
"""Shared schema builders for generation stats, ranking, and metadata."""
from __future__ import annotations

import statistics
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from core.quality_gate import calculate_ac_value

DEFAULT_SCORE_WEIGHTS: Dict[str, float] = {
    "probability": 0.35,
    "pattern": 0.20,
    "ai": 0.25,
    "genetic": 0.20,
    "confidence_probability": 0.45,
    "confidence_ensemble": 0.55,
}


def resolve_total_algorithms_active(engine_like: Any, default: int = 0) -> int:
    """Safely resolves active algorithm count from LottoEngine or AlgorithmHub-like objects."""
    try:
        if engine_like is None:
            return int(default)

        class_registry = getattr(engine_like, "class_algorithm_registry", None)
        function_registry = getattr(engine_like, "function_algorithm_registry", None)
        if isinstance(class_registry, dict) and isinstance(function_registry, dict):
            return int(len(class_registry) + len(function_registry))

        nested_engine = getattr(engine_like, "engine", None)
        if nested_engine is not None and nested_engine is not engine_like:
            return resolve_total_algorithms_active(nested_engine, default=default)

        return int(default)
    except Exception:
        return int(default)


def build_generation_stats(numbers: Sequence[int], confidence: float, contributors: int) -> Dict[str, Any]:
    cleaned = sorted(int(n) for n in numbers if 1 <= int(n) <= 45)[:6]
    if len(cleaned) < 6:
        cleaned = sorted(set(cleaned + [1, 8, 15, 23, 34, 42]))[:6]

    odd_count = sum(1 for n in cleaned if n % 2 != 0)
    high_count = sum(1 for n in cleaned if n >= 23)
    return {
        "sum": int(sum(cleaned)),
        "odd_count": int(odd_count),
        "even_count": int(6 - odd_count),
        "high_count": int(high_count),
        "low_count": int(6 - high_count),
        "ac_value": int(calculate_ac_value(cleaned)),
        "confidence": float(confidence),
        "contributors": int(max(1, contributors)),
    }


def build_generation_metadata(
    *,
    algorithm_id: str,
    algorithm_title: str,
    total_algorithms_active: int,
    confidence_score: float,
    round_info: str = "Live Draw",
    discarded_count: Optional[int] = None,
    leading_algorithms: Optional[Iterable[str]] = None,
    extras: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    metadata = {
        "schema_version": "1.0",
        "algorithm_id": str(algorithm_id or "ensemble_auto"),
        "algorithm_title": str(algorithm_title or "Advanced AI Ensemble"),
        "round_info": str(round_info or "Live Draw"),
        "total_algorithms_active": int(max(1, total_algorithms_active)),
        "confidence_score": float(confidence_score),
    }

    if discarded_count is not None:
        metadata["discarded_count"] = int(max(0, discarded_count))

    if leading_algorithms is not None:
        metadata["leading_algorithms"] = [str(item) for item in leading_algorithms if str(item).strip()]

    if isinstance(extras, dict):
        metadata.update(extras)

    return metadata


def build_frequency_map_from_history(history_draws: Sequence[Sequence[int]], lookback: int = 120) -> Dict[int, float]:
    """Builds a normalized 1~45 frequency map from recent historical draws."""
    counts = {n: 1.0 for n in range(1, 46)}
    if not history_draws:
        return counts

    try:
        recent = list(history_draws)[-max(1, int(lookback)):]
        for draw in recent:
            for n in draw:
                iv = int(n)
                if 1 <= iv <= 45:
                    counts[iv] += 1.0
    except Exception:
        return counts

    max_count = max(counts.values()) if counts else 1.0
    if max_count <= 0:
        return {n: 1.0 for n in range(1, 46)}
    return {n: float(v / max_count) for n, v in counts.items()}


def _clamp_score(value: float, lower: float = 0.0, upper: float = 100.0) -> float:
    try:
        return max(lower, min(upper, float(value)))
    except Exception:
        return lower


def _normalize_ratio_weights(values: Dict[str, float], keys: Sequence[str]) -> Dict[str, float]:
    cleaned = {}
    for key in keys:
        try:
            cleaned[key] = max(0.0001, float(values.get(key, 0.0)))
        except Exception:
            cleaned[key] = 0.0001

    total = sum(cleaned.values())
    if total <= 0:
        unit = 1.0 / float(max(1, len(keys)))
        return {key: unit for key in keys}
    return {key: float(cleaned[key] / total) for key in keys}


def _resolve_score_weights(score_weights: Optional[Dict[str, float]] = None) -> Dict[str, float]:
    merged = dict(DEFAULT_SCORE_WEIGHTS)
    if isinstance(score_weights, dict):
        for key in DEFAULT_SCORE_WEIGHTS.keys():
            if key in score_weights:
                try:
                    merged[key] = float(score_weights[key])
                except Exception:
                    pass

    ensemble_keys = ("probability", "pattern", "ai", "genetic")
    confidence_keys = ("confidence_probability", "confidence_ensemble")
    merged.update(_normalize_ratio_weights(merged, ensemble_keys))
    merged.update(_normalize_ratio_weights(merged, confidence_keys))
    return merged


def derive_score_weights_from_history(
    history_draws: Sequence[Sequence[int]],
    *,
    lookback: int = 120,
) -> Dict[str, float]:
    """
    Derives score decomposition weights from historical volatility/concentration.
    This enables adaptive, data-driven calibration for Top-ranked combination scoring.
    """
    base = dict(DEFAULT_SCORE_WEIGHTS)
    if not history_draws:
        return _resolve_score_weights(base)

    try:
        recent = list(history_draws)[-max(12, int(lookback)):]
    except Exception:
        return _resolve_score_weights(base)

    cleaned_draws: List[List[int]] = []
    for draw in recent:
        try:
            nums = sorted({int(n) for n in draw if 1 <= int(n) <= 45})
        except Exception:
            nums = []
        if len(nums) == 6:
            cleaned_draws.append(nums)

    if len(cleaned_draws) < 8:
        return _resolve_score_weights(base)

    number_counts = {n: 0 for n in range(1, 46)}
    sums: List[int] = []
    odd_counts: List[int] = []
    for draw in cleaned_draws:
        sums.append(int(sum(draw)))
        odd_counts.append(int(sum(1 for n in draw if n % 2 != 0)))
        for n in draw:
            number_counts[n] += 1

    total_hits = float(sum(number_counts.values()))
    if total_hits <= 0:
        return _resolve_score_weights(base)

    probabilities = [float(count) / total_hits for count in number_counts.values() if count > 0]
    concentration = float(sum(p * p for p in probabilities)) if probabilities else (1.0 / 45.0)
    baseline_concentration = 1.0 / 45.0
    concentration_ratio = concentration / baseline_concentration if baseline_concentration > 0 else 1.0

    sum_std = float(statistics.pstdev(sums)) if len(sums) > 1 else 0.0
    odd_std = float(statistics.pstdev(odd_counts)) if len(odd_counts) > 1 else 0.0
    volatility_index = (sum_std / 26.0) + (odd_std / 2.5)

    concentration_shift = max(-0.08, min(0.08, (concentration_ratio - 1.0) * 0.045))
    volatility_shift = max(-0.06, min(0.06, (volatility_index - 0.90) * 0.055))

    tuned = dict(base)
    tuned["ai"] = base["ai"] - concentration_shift
    tuned["pattern"] = base["pattern"] + (concentration_shift * 0.60)
    tuned["genetic"] = base["genetic"] + (concentration_shift * 0.40)

    tuned["probability"] = tuned["probability"] - volatility_shift
    tuned["pattern"] = tuned["pattern"] + (volatility_shift * 0.35)
    tuned["genetic"] = tuned["genetic"] + (volatility_shift * 0.65)

    confidence_probability = 0.45 - (volatility_shift * 0.80) + (concentration_shift * 0.50)
    confidence_probability = max(0.30, min(0.70, confidence_probability))
    tuned["confidence_probability"] = confidence_probability
    tuned["confidence_ensemble"] = 1.0 - confidence_probability

    return _resolve_score_weights(tuned)


def _pattern_score(numbers: Sequence[int]) -> float:
    cleaned = sorted(int(n) for n in numbers)
    if len(cleaned) != 6:
        return 0.0

    odd_count = sum(1 for n in cleaned if n % 2 != 0)
    high_count = sum(1 for n in cleaned if n >= 23)
    decades = {(n - 1) // 10 for n in cleaned}
    consecutive_pairs = sum(1 for i in range(5) if cleaned[i + 1] - cleaned[i] == 1)
    ac = calculate_ac_value(cleaned)

    score = 50.0
    score += max(0.0, 15.0 - abs(odd_count - 3.0) * 6.0)
    score += max(0.0, 12.0 - abs(high_count - 3.0) * 5.0)
    score += min(20.0, float(len(decades)) * 5.5)
    score += min(18.0, float(ac) * 2.0)
    score -= float(consecutive_pairs) * 4.5
    return _clamp_score(score)


def _ai_score(numbers: Sequence[int], frequency_map: Optional[Dict[int, float]], probability_score: float) -> float:
    if not frequency_map:
        return _clamp_score(50.0 + (probability_score - 50.0) * 0.35)

    values = []
    for n in numbers:
        try:
            values.append(float(frequency_map.get(int(n), 0.5)))
        except Exception:
            values.append(0.5)
    if not values:
        return _clamp_score(50.0 + (probability_score - 50.0) * 0.35)

    return _clamp_score((sum(values) / len(values)) * 100.0)


def _genetic_score(numbers: Sequence[int], rank_index: int, total_candidates: int) -> float:
    cleaned = sorted(int(n) for n in numbers)
    rank_strength = 1.0 - (float(rank_index) / max(1.0, float(total_candidates - 1)))
    spread = float(max(cleaned) - min(cleaned)) if cleaned else 0.0
    score = 55.0 + (rank_strength * 32.0) + min(13.0, spread * 0.45)
    return _clamp_score(score)


def build_top_ranked_combinations(
    scored_candidates: Sequence[Tuple[float, Sequence[int]]],
    *,
    limit: int = 50,
    frequency_map: Optional[Dict[int, float]] = None,
    score_weights: Optional[Dict[str, float]] = None,
) -> List[Dict[str, Any]]:
    """
    Builds ranked combination payload with decomposed scores:
    confidence, probability, pattern, AI, genetic, ensemble.
    """
    normalized: List[Tuple[float, List[int]]] = []
    seen = set()
    for raw_score, raw_numbers in scored_candidates:
        try:
            cleaned = sorted({int(n) for n in raw_numbers if 1 <= int(n) <= 45})
        except Exception:
            continue
        if len(cleaned) != 6:
            continue
        key = tuple(cleaned)
        if key in seen:
            continue
        seen.add(key)
        normalized.append((float(raw_score), cleaned))

    normalized.sort(key=lambda item: item[0], reverse=True)
    if not normalized:
        return []

    top_items = normalized[: max(1, int(limit))]
    total = len(top_items)
    ranked_payload = []
    weights = _resolve_score_weights(score_weights)

    for rank_idx, (raw_score, numbers) in enumerate(top_items, start=1):
        probability_score = _clamp_score(raw_score)
        pattern_score = _pattern_score(numbers)
        ai_score = _ai_score(numbers, frequency_map, probability_score)
        genetic_score = _genetic_score(numbers, rank_idx - 1, total)
        ensemble_score = _clamp_score(
            (weights["probability"] * probability_score)
            + (weights["pattern"] * pattern_score)
            + (weights["ai"] * ai_score)
            + (weights["genetic"] * genetic_score)
        )
        confidence_score = _clamp_score(
            (weights["confidence_ensemble"] * ensemble_score)
            + (weights["confidence_probability"] * probability_score)
        )

        ranked_payload.append(
            {
                "rank": int(rank_idx),
                "numbers": list(numbers),
                "confidence_score": round(float(confidence_score), 2),
                "probability_score": round(float(probability_score), 2),
                "pattern_score": round(float(pattern_score), 2),
                "ai_score": round(float(ai_score), 2),
                "genetic_score": round(float(genetic_score), 2),
                "ensemble_score": round(float(ensemble_score), 2),
            }
        )

    return ranked_payload
