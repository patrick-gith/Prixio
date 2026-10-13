"""Mode B — compare mon prix à la médiane mondiale, toutes régions."""
from statistics import median
from decimal import Decimal

from django.conf import settings

from ..models import PricePoint
from ..fx import convert


def market_position(product, my_price: Decimal, my_currency: str, region: str) -> dict:
    """
    Retourne :
      - position_pct : mon prix vs médiane marché (positif = trop cher)
      - suggested_price : médiane - 2%
      - cheapest : meilleure offre mondiale
      - by_region : prix médian par région
    """
    base = settings.BASE_CURRENCY

    # 1) Derniers prix par source (30 derniers jours, une offre par source)
    points = list(
        PricePoint.objects
        .filter(product=product, captured_at__gte=__import__("django.utils.timezone",
            fromlist=["now"]).now() - __import__("datetime").timedelta(days=30))
        .select_related("source")
        .order_by("-captured_at")
    )

    if not points:
        return {"has_data": False}

    # 2) Normalisation en devise de base
    normalized = []
    by_region: dict[str, list[Decimal]] = {}
    for p in points:
        price_base = convert(p.price_local, p.currency, base)
        normalized.append({
            "price_base": price_base,
            "source": p.source.name,
            "region": p.source.region,
            "price_local": p.price_local,
            "currency": p.currency,
        })
        by_region.setdefault(p.source.region, []).append(price_base)

    prices_base = [n["price_base"] for n in normalized]
    market_median = median(prices_base)
    cheapest = min(normalized, key=lambda n: n["price_base"])

    # 3) Ma position
    my_price_base = convert(my_price, my_currency, base)
    position = float((my_price_base - market_median) / market_median) if market_median else 0.0

    suggested_base = (market_median * Decimal("0.98")).quantize(Decimal("0.01"))
    suggested_local = convert(suggested_base, base, my_currency)

    # 4) Médiane par région, ramenée dans ma devise
    regions_summary = {}
    for reg, values in by_region.items():
        med_base = median(values)
        regions_summary[reg] = {
            "median_base": float(med_base),
            "median_local": float(convert(med_base, base, my_currency)),
            "count": len(values),
        }

    return {
        "has_data": True,
        "my_price": float(my_price),
        "my_currency": my_currency,
        "market_median_base": float(market_median),
        "market_median_local": float(convert(market_median, base, my_currency)),
        "position_pct": round(position * 100, 1),
        "suggested_local": float(suggested_local),
        "cheapest": {
            "price_base": float(cheapest["price_base"]),
            "price_local": float(cheapest["price_local"]),
            "currency": cheapest["currency"],
            "source": cheapest["source"],
            "region": cheapest["region"],
        },
        "by_region": regions_summary,
        "rival_count": len(normalized),
    }