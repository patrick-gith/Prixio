"""Tests du moteur d'anomalie (Mode A)."""
from decimal import Decimal

from PricingApp.engines.anomaly import compute_baseline, opportunity_score


class TestComputeBaseline:
    def test_empty_list(self):
        assert compute_baseline([]) == {}

    def test_basic_stats(self):
        prices = [Decimal(str(p)) for p in [10, 12, 14, 16, 18]]
        result = compute_baseline(prices)
        assert result["median"] == 14.0
        assert result["count"] == 5
        assert result["p10"] <= result["p90"]

    def test_volatility_zero_when_constant(self):
        prices = [Decimal("10")] * 10
        result = compute_baseline(prices)
        assert result["volatility"] == 0.0


class TestOpportunityScore:
    def test_score_zero_without_enough_data(self):
        result = opportunity_score(10.0, {"count": 1})
        assert result["score"] == 0.0

    def test_high_score_on_real_deal(self):
        """Prix actuel 30% sous la médiane, produit stable → score élevé."""
        baseline = {
            "median": 100.0, "p10": 75.0, "p90": 120.0,
            "volatility": 0.05, "count": 90,
        }
        result = opportunity_score(current=65.0, baseline=baseline)
        assert result["score"] >= 80
        assert result["label"] == "🔥"
        assert result["deviation_pct"] == 35.0

    def test_low_score_on_bad_deal(self):
        """Prix actuel 20% au-dessus de la médiane → score faible."""
        baseline = {
            "median": 100.0, "p10": 75.0, "p90": 120.0,
            "volatility": 0.15, "count": 90,
        }
        result = opportunity_score(current=120.0, baseline=baseline)
        assert result["score"] < 40
        assert result["deviation_pct"] == 0.0  # clampé à 0 si au-dessus

    def test_score_capped_at_100(self):
        baseline = {
            "median": 100.0, "p10": 90.0, "p90": 110.0,
            "volatility": 0.01, "count": 200,
        }
        result = opportunity_score(current=50.0, baseline=baseline)
        assert result["score"] <= 100