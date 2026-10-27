"""Fixtures partagées par tous les tests."""
import os

TEST_USER_PW = os.environ.get("TEST_USER_PW", "test-pw-not-a-secret")
from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.utils import timezone

from CatalogApp.models import Product
from PricingApp.models import PricePoint, Source, Watchlist


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="marie", email="marie@example.com", password=TEST_USER_PW,
    )


@pytest.fixture
def book(db):
    return Product.objects.create(
        canonical_type="book",
        primary_id="9782070408504",
        title="Le Petit Prince",
        brand="Antoine de Saint-Exupéry",
    )


@pytest.fixture
def crypto(db):
    return Product.objects.create(
        canonical_type="crypto",
        primary_id="bitcoin",
        title="Bitcoin",
        brand="BTC",
    )


@pytest.fixture
def source_fr(db):
    return Source.objects.create(
        name="Google Books FR",
        adapter_key="google_books",
        region="FR",
        currency="EUR",
    )


@pytest.fixture
def price_history_factory(db, book, source_fr):
    """Crée une série de prix à des dates choisies."""
    def _make(prices: list[float], start_days_ago: int = 90):
        today = timezone.now()
        step = start_days_ago // max(len(prices) - 1, 1)
        points = []
        for i, p in enumerate(prices):
            point = PricePoint.objects.create(
                product=book,
                source=source_fr,
                price_local=Decimal(str(p)),
                currency="EUR",
                in_stock=True,
            )
            # Force captured_at (auto_now_add) en SQL direct
            PricePoint.objects.filter(pk=point.pk).update(
                captured_at=today - timedelta(days=start_days_ago - i * step)
            )
            point.refresh_from_db()
            points.append(point)
        return points
    return _make


@pytest.fixture
def watchlist(user, book):
    return Watchlist.objects.create(user=user, product=book, target_score=70)