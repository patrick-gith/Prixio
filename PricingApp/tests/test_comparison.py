"""Tests du moteur de comparaison (Mode B)."""
from decimal import Decimal

import pytest

from PricingApp.engines.comparison import market_position
from PricingApp.models import PricePoint, Source


@pytest.mark.django_db
class TestMarketPosition:
    def test_no_data(self, book):
        result = market_position(book, Decimal("10"), "EUR", "FR")
        assert result == {"has_data": False}

    def test_position_above_market(self, book):
        """Mon prix est 15% au-dessus de la médiane → position_pct > 0."""
        s1 = Source.objects.create(
            name="Amazon FR", adapter_key="amazon", region="FR", currency="EUR",
        )
        s2 = Source.objects.create(
            name="Fnac", adapter_key="fnac", region="FR", currency="EUR",
        )
        PricePoint.objects.create(product=book, source=s1, price_local=Decimal("100"), currency="EUR")
        PricePoint.objects.create(product=book, source=s2, price_local=Decimal("100"), currency="EUR")

        result = market_position(book, Decimal("115"), "EUR", "FR")

        assert result["has_data"] is True
        assert result["position_pct"] == 15.0
        assert result["suggested_local"] < 115
        assert result["cheapest"]["source"] in ("Amazon FR", "Fnac")

    def test_position_below_market(self, book):
        """Mon prix est 20% en-dessous → position_pct < 0."""
        s1 = Source.objects.create(
            name="Amazon FR", adapter_key="amazon", region="FR", currency="EUR",
        )
        PricePoint.objects.create(product=book, source=s1, price_local=Decimal("100"), currency="EUR")

        result = market_position(book, Decimal("80"), "EUR", "FR")
        assert result["position_pct"] < 0