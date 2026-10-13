"""Conversion de devises avec cache journalier (Frankfurter API, gratuit)."""
from datetime import date
from decimal import Decimal

import requests
from django.conf import settings

from .models import FxRate


FRANKFURTER = "https://api.frankfurter.app"


def get_rate(base: str, quote: str, on: date | None = None) -> Decimal:
    """Retourne le taux base → quote. Cache en base, fallback API."""
    if base == quote:
        return Decimal("1.0")

    on = on or date.today()

    # 1) Cache
    cached = FxRate.objects.filter(date=on, base=base, quote=quote).first()
    if cached:
        return cached.rate

    # 2) API (Frankfurter supporte ~30 devises, dont EUR/USD/GBP/JPY)
    try:
        r = requests.get(
            f"{FRANKFURTER}/{on.isoformat()}",
            params={"from": base, "to": quote},
            timeout=6,
        )
        r.raise_for_status()
        rate = Decimal(str(r.json()["rates"][quote]))
    except (requests.RequestException, KeyError):
        # Fallback : ne rien casser, retourner 1 (dégradé mais sûr)
        return Decimal("1.0")

    FxRate.objects.update_or_create(
        date=on, base=base, quote=quote,
        defaults={"rate": rate},
    )
    return rate


def convert(amount: Decimal, frm: str, to: str, on: date | None = None) -> Decimal:
    if frm == to:
        return amount
    return (amount * get_rate(frm, to, on)).quantize(Decimal("0.01"))