from CatalogApp.models import Product

from .engines.anomaly import compute_baseline, opportunity_score
from .models import PricePoint


def analyze_product(product: Product) -> dict:
    points = list(
        PricePoint.objects.filter(product=product).order_by("-captured_at")[:200]
    )
    if not points:
        return {"has_data": False}

    prices = [p.price_local for p in points]
    baseline = compute_baseline(prices)
    current = float(points[0].price_local)
    score = opportunity_score(current, baseline)

    best = min(points, key=lambda p: float(p.price_local))

    return {
        "has_data": True,
        "current_price": float(points[0].price_local),
        "currency": points[0].currency,
        "best_offer": {
            "price": float(best.price_local),
            "currency": best.currency,
            "source": best.source.name,
            "region": best.source.region,
        },
        "history": [
            {
                "price": float(p.price_local),
                "date": p.captured_at.strftime("%Y-%m-%d"),
                "source": p.source.name,
            }
            for p in reversed(points[:30])
        ],
        **score,
    }
