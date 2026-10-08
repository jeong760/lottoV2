# -*- coding: utf-8 -*-
"""Shared schema builders for generation stats and metadata."""
from __future__ import annotations

from typing import Any, Dict, Iterable, Optional, Sequence

from core.quality_gate import calculate_ac_value


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
