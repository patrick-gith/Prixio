from statistics import median, pstdev, mean
from decimal import Decimal


def compute_baseline(prices: list[Decimal], period_days: int = 90) -> dict:
    if not prices:
        return {}
    floats = [float(p) for p in prices]
    sorted_floats = sorted(floats)
    return {
        "median": float(median(floats)),
        "p10": float(sorted_floats[int(len(sorted_floats) * 0.10)]),
        "p90": float(sorted_floats[int(len(sorted_floats) * 0.90)]),
        "volatility": pstdev(floats) / mean(floats) if mean(floats) else 0.0,
        "count": len(floats),
    }


def opportunity_score(current: float, baseline: dict) -> dict:
    if not baseline or baseline.get("count", 0) < 2:
        return {"score": 0.0, "label": "—", "baseline": {}, "deviation_pct": 0.0}

    med = baseline["median"]
    deviation = max((med - current) / med, 0.0) if med else 0.0
    volatility = baseline["volatility"]
    freshness = 1.0
    rare = 1.0 if current <= baseline["p10"] else 0.0

    score = 100 * min(
        0.45 * deviation
        + 0.20 * (1 - min(volatility, 1.0))
        + 0.20 * freshness
        + 0.15 * rare,
        1.0,
    )

    if score >= 80:
        label = "🔥"
    elif score >= 60:
        label = "✅"
    elif score >= 40:
        label = "🟡"
    else:
        label = "⚠️"

    return {
        "score": round(score, 1),
        "label": label,
        "baseline": baseline,
        "deviation_pct": round(deviation * 100, 1),
    }
