from __future__ import annotations

import math
from datetime import datetime


IMPORTANCE_SCORES = {
    "high": 1.0,
    "medium": 0.6,
    "low": 0.3,
}

SOURCE_SCORES = {
    "github_release": 1.0,
    "docs_feed": 0.7,
}


def compute_base_score(
    summary: dict,
    *,
    weights: dict,
    now_iso: str,
    recency_half_life_days: float,
) -> float:
    evidence_items = summary.get("evidence_items") or []
    importance_score = IMPORTANCE_SCORES.get(summary.get("importance"), 0.3)
    recency_score = _compute_recency_score(evidence_items, now_iso, recency_half_life_days)
    evidence_score = _compute_evidence_score(evidence_items)
    source_score = _compute_source_score(evidence_items)

    return (
        weights.get("importance", 0.0) * importance_score
        + weights.get("recency", 0.0) * recency_score
        + weights.get("evidence", 0.0) * evidence_score
        + weights.get("source", 0.0) * source_score
    )


def apply_read_decay(
    base_score: float,
    *,
    project_id: str,
    read_events: list[dict],
    now_iso: str,
    read_decay_days: int,
    read_decay_factor: float,
) -> float:
    if not project_id or not read_events:
        return base_score

    now_ts = _timestamp_for_sort(now_iso)
    if now_ts <= 0:
        return base_score

    max_age_seconds = read_decay_days * 24 * 60 * 60
    for event in read_events:
        if event.get("project_id") != project_id:
            continue
        read_at = event.get("read_at")
        if not read_at:
            continue
        age_seconds = now_ts - _timestamp_for_sort(read_at)
        if 0 <= age_seconds <= max_age_seconds:
            return base_score * read_decay_factor
    return base_score


def rerank_with_mmr(items: list[dict], *, lambda_param: float, diversity_keys: list[str]) -> list[dict]:
    if not items:
        return []
    if not diversity_keys:
        return list(items)

    lambda_param = min(max(lambda_param, 0.0), 1.0)
    remaining = sorted(items, key=lambda item: item.get("ranking_score", 0.0), reverse=True)
    selected: list[dict] = []
    diversity_sets = {id(item): _build_diversity_set(item, diversity_keys) for item in remaining}

    while remaining:
        if not selected:
            selected.append(remaining.pop(0))
            continue

        best_index = 0
        best_score = None
        for index, candidate in enumerate(remaining):
            score = candidate.get("ranking_score", 0.0)
            candidate_set = diversity_sets.get(id(candidate), set())
            max_sim = max(
                (
                    _jaccard(candidate_set, diversity_sets.get(id(chosen), set()))
                    for chosen in selected
                ),
                default=0.0,
            )
            mmr_score = lambda_param * score - (1.0 - lambda_param) * max_sim
            if best_score is None or mmr_score > best_score:
                best_score = mmr_score
                best_index = index

        selected.append(remaining.pop(best_index))

    return selected


def _compute_recency_score(items: list[dict], now_iso: str, half_life_days: float) -> float:
    if half_life_days <= 0:
        return 0.0
    now_ts = _timestamp_for_sort(now_iso)
    latest_ts = max((_timestamp_for_sort(item.get("published_at")) for item in items), default=0)
    if now_ts <= 0 or latest_ts <= 0:
        return 0.0
    age_seconds = max(0, now_ts - latest_ts)
    age_days = age_seconds / (24 * 60 * 60)
    return math.exp(-age_days / half_life_days)


def _compute_evidence_score(items: list[dict]) -> float:
    action_count = sum(len(item.get("action_items") or []) for item in items)
    impact_count = sum(len(item.get("impact_points") or []) for item in items)
    detail_count = sum(len(item.get("detail_sections") or []) for item in items)

    action_value = min(1.0, action_count / 3.0)
    impact_value = min(1.0, impact_count / 3.0)
    detail_value = min(1.0, detail_count / 3.0)

    return min(1.0, 0.4 * action_value + 0.3 * impact_value + 0.3 * detail_value)


def _compute_source_score(items: list[dict]) -> float:
    if not items:
        return 0.5
    return max(SOURCE_SCORES.get(item.get("source"), 0.5) for item in items)


def _build_diversity_set(item: dict, diversity_keys: list[str]) -> set[str]:
    evidence_items = item.get("evidence_items") or []
    tokens: set[str] = set()
    for evidence in evidence_items:
        for key in diversity_keys:
            if key == "tags":
                for tag in evidence.get("tags") or []:
                    tokens.add(f"{key}:{tag}")
                continue
            value = evidence.get(key)
            if value:
                tokens.add(f"{key}:{value}")
    return tokens


def _jaccard(left: set[str], right: set[str]) -> float:
    if not left and not right:
        return 0.0
    union = left | right
    if not union:
        return 0.0
    return len(left & right) / len(union)


def _timestamp_for_sort(value: str | None) -> int:
    if not value:
        return 0
    try:
        return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp())
    except ValueError:
        return 0
