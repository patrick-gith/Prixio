"""Mode C — prévision linéaire simple + saisonnalité mensuelle."""
from collections import defaultdict
from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

from ..models import PricePoint
from ..fx import convert


def procurement_signal(product, quantity: int, deadline, my_currency: str) -> dict:
    """
    Analyse les 180 derniers jours, extrapole à la deadline.
    Retourne un signal BUY_NOW / WAIT / NEUTRAL et l'économie estimée.
    """
    since = timezone.now() - timedelta(days=180)
    points = (
        PricePoint.objects
        .filter(product=product, captured_at__gte=since)
        .order_by("captured_at")
    )
    if points.count() < 4:
        return {"has_data": False}

    # 1) Prix moyen par mois (en devise locale, puis converti)
    monthly: dict[str, list[Decimal]] = defaultdict(list)
    for p in points:
        key = p.captured_at.strftime("%Y-%m")
        monthly[key].append(convert(p.price_local, p.currency, my_currency))

    months_sorted = sorted(monthly.keys())
    if len(months_sorted) < 2:
        return {"has_data": False}

    values = [float(sum(monthly[m]) / len(monthly[m])) for m in months_sorted]

    # 2) Régression linéaire simple sur l'index du mois
    n = len(values)
    xs = list(range(n))
    mean_x = sum(xs) / n
    mean_y = sum(values) / n
    num = sum((xs[i] - mean_x) * (values[i] - mean_y) for i in range(n))
    den = sum((xs[i] - mean_x) ** 2 for i in range(n)) or 1
    slope = num / den
    intercept = mean_y - slope * mean_x

    # 3) Combien de mois jusqu'à la deadline ?
    today = timezone.now().date()
    days_ahead = max((deadline - today).days, 0)
    months_ahead = days_ahead / 30.0

    forecast = intercept + slope * (n - 1 + months_ahead)
    current = values[-1]

    if current == 0:
        return {"has_data": False}

    delta_pct = (forecast - current) / current

    # Seuil de décision : 3% est le point où l'action devient rentable
    # (frais de réorganisation, attente, risque de rupture).
    DECISION_THRESHOLD = 0.03

    if delta_pct < -DECISION_THRESHOLD:
        signal = "WAIT"
    elif delta_pct > DECISION_THRESHOLD:
        signal = "BUY_NOW"
    else:
        signal = "NEUTRAL"
    saving_per_unit = abs(forecast - current)
    total_saving = saving_per_unit * quantity

    return {
        "has_data": True,
        "signal": signal,
        "current_price": round(current, 2),
        "forecast_price": round(forecast, 2),
        "delta_pct": round(delta_pct * 100, 1),
        "days_ahead": days_ahead,
        "quantity": quantity,
        "total_saving": round(total_saving, 2),
        "currency": my_currency,
    }