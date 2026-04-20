from __future__ import annotations

import time
from collections import Counter
from statistics import mean
from typing import Any

REQUEST_LATENCIES: list[tuple[float, int]] = []
REQUEST_COSTS: list[tuple[float, float]] = []
REQUEST_TOKENS_IN: list[tuple[float, int]] = []
REQUEST_TOKENS_OUT: list[tuple[float, int]] = []
ERRORS: Counter[str] = Counter()
TRAFFIC: int = 0
QUALITY_SCORES: list[tuple[float, float]] = []

WINDOW_SIZE = 5
TIME_WINDOW_SECONDS = 30

def record_request(latency_ms: int, cost_usd: float, tokens_in: int, tokens_out: int, quality_score: float) -> None:
    global TRAFFIC
    TRAFFIC += 1
    now = time.time()
    
    # Store with timestamp for time-based filtering
    # We only keep the last WINDOW_SIZE items to ensure responsiveness
    lists_and_values = [
        (REQUEST_LATENCIES, latency_ms),
        (REQUEST_COSTS, cost_usd),
        (REQUEST_TOKENS_IN, tokens_in),
        (REQUEST_TOKENS_OUT, tokens_out),
        (QUALITY_SCORES, quality_score)
    ]
    
    for target_list, value in lists_and_values:
        target_list.append((now, value))
        if len(target_list) > WINDOW_SIZE:
            target_list.pop(0)

def record_error(error_type: str) -> None:
    ERRORS[error_type] += 1

def reset_metrics() -> None:
    global TRAFFIC
    TRAFFIC = 0
    REQUEST_LATENCIES.clear()
    REQUEST_COSTS.clear()
    REQUEST_TOKENS_IN.clear()
    REQUEST_TOKENS_OUT.clear()
    QUALITY_SCORES.clear()
    ERRORS.clear()

def _get_windowed_values(target_list: list[tuple[float, Any]]) -> list:
    now = time.time()
    # Filter: ONLY keep values from the last 30 seconds
    return [v for t, v in target_list if now - t <= TIME_WINDOW_SECONDS]

def percentile(values: list[int], p: int) -> float:
    if not values:
        return 0.0
    items = sorted(values)
    idx = max(0, min(len(items) - 1, round((p / 100) * len(items) + 0.5) - 1))
    return float(items[idx])

def snapshot() -> dict:
    # Crucial: snapshots are ALWAYS calculated on the windowed data
    win_latency = _get_windowed_values(REQUEST_LATENCIES)
    win_costs = _get_windowed_values(REQUEST_COSTS)
    win_tokens_in = _get_windowed_values(REQUEST_TOKENS_IN)
    win_tokens_out = _get_windowed_values(REQUEST_TOKENS_OUT)
    win_quality = _get_windowed_values(QUALITY_SCORES)
    
    return {
        "traffic": TRAFFIC,
        "latency_p50": percentile(win_latency, 50),
        "latency_p95": percentile(win_latency, 95),
        "latency_p99": percentile(win_latency, 99),
        "avg_cost_usd": round(mean(win_costs), 4) if win_costs else 0.0,
        "total_cost_usd": round(sum([v for t, v in REQUEST_COSTS]), 4),
        "tokens_in_total": sum(win_tokens_in),
        "tokens_out_total": sum(win_tokens_out),
        "error_breakdown": dict(ERRORS),
        "quality_avg": round(mean(win_quality), 4) if win_quality else 0.0,
    }
