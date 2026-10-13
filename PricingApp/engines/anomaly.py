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
    freshness = 1.0  # TODO : calculer depuis la date du premier prix bas
    rare = 1.0 if current <= baseline["p10"] else 0.0

    # ──────────────────────────────────────────────────────────────
    # Formule calibrée pour que :
    #   -30% de remise + produit stable + rare  → score ~85
    #   -20%                                     → score ~70
    #   prix au-dessus de la médiane             → score < 30
    #
    # Le poids dominant (0.70) va à la déviation, car c'est LE signal
    # qui intéresse l'acheteur. Les 0.30 restants récompensent la
    # stabilité, la fraîcheur et le caractère exceptionnel.
    #
    # On normalise la déviation sur 35% : au-delà, considéré comme
    # "maximalement anormal". Cela évite qu'un produit gratuit (dev=1)
    # écrase tout le monde — 35% sous la médiane est déjà énorme.
    # ──────────────────────────────────────────────────────────────
    deviation_normalized = min(deviation / 0.35, 1.0)

    score = 100 * min(
        0.70 * deviation_normalized      # ← le vrai signal
        + 0.10 * (1 - min(volatility, 1.0))
        + 0.10 * freshness
        + 0.10 * rare,
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