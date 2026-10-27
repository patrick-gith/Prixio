"""Tests du moteur de prévision (Mode C)."""
from datetime import date, timedelta

import pytest

from PricingApp.engines.forecast import procurement_signal


@pytest.mark.django_db
class TestProcurementSignal:
    def test_no_data_returns_false(self, book):
        """Aucun PricePoint → has_data=False."""
        result = procurement_signal(book, 10, date.today() + timedelta(days=30), "EUR")
        assert result == {"has_data": False}

    def test_wait_signal_on_downtrend(self, book, price_history_factory):
        """Tendance baissière → signal WAIT."""
        # 6 mois de prix qui baissent régulièrement
        prices = [120 - i * 2 for i in range(0, 60, 10)]  # 120, 100, 80, 60…
        # On doit créer un point par mois environ
        prices = [120, 115, 110, 105, 100, 95, 90]
        price_history_factory(prices, start_days_ago=180)

        result = procurement_signal(book, 10, date.today() + timedelta(days=30), "EUR")

        assert result["has_data"] is True
        assert result["signal"] == "WAIT"
        assert result["delta_pct"] < 0
        assert result["total_saving"] > 0

    def test_buy_now_signal_on_uptrend(self, book, price_history_factory):
        """Tendance haussière → signal BUY_NOW."""
        prices = [80, 85, 90, 95, 100, 105, 110]
        price_history_factory(prices, start_days_ago=180)

        result = procurement_signal(book, 10, date.today() + timedelta(days=30), "EUR")

        assert result["signal"] == "BUY_NOW"
        assert result["delta_pct"] > 0

    def test_neutral_signal_on_flat_prices(self, book, price_history_factory):
        """Prix stable → NEUTRAL."""
        prices = [100, 100, 101, 99, 100, 101, 100]
        price_history_factory(prices, start_days_ago=180)

        result = procurement_signal(book, 10, date.today() + timedelta(days=30), "EUR")

        assert result["signal"] == "NEUTRAL"
        assert abs(result["delta_pct"]) < 5