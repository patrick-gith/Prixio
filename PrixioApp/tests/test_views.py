"""Tests comportementaux pour PrixioApp.views."""
import pytest
from django.urls import reverse

from PricingApp.models import Watchlist

pytestmark = pytest.mark.django_db


class TestDashboard:
    def test_requires_login(self, client):
        response = client.get(reverse("PrixioApp:dashboard"))
        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_renders_with_empty_watchlist(self, client, user):
        client.force_login(user)
        response = client.get(reverse("PrixioApp:dashboard"))
        assert response.status_code == 200
        assert response.context["opportunities"] == []
        assert response.context["stats"]["watchlist_count"] == 0

    def test_counts_watchlist(self, client, user, watchlist):
        client.force_login(user)
        response = client.get(reverse("PrixioApp:dashboard"))
        assert response.context["stats"]["watchlist_count"] == 1


class TestAddToWatchlist:
    def test_requires_login(self, client, book):
        response = client.get(reverse("PrixioApp:add_to_watchlist", args=[book.pk]))
        assert response.status_code == 302

    def test_creates_entry(self, client, user, book):
        client.force_login(user)
        response = client.get(reverse("PrixioApp:add_to_watchlist", args=[book.pk]))
        assert response.status_code == 302
        assert Watchlist.objects.filter(user=user, product=book).exists()

    def test_idempotent_when_already_in_watchlist(self, client, user, watchlist):
        client.force_login(user)
        response = client.get(
            reverse("PrixioApp:add_to_watchlist", args=[watchlist.product_id]),
            follow=True,
        )
        assert response.status_code == 200
        assert Watchlist.objects.filter(user=user).count() == 1

    def test_redirects_to_safe_next_param(self, client, user, book):
        client.force_login(user)
        response = client.get(
            reverse("PrixioApp:add_to_watchlist", args=[book.pk]) + "?next=/dashboard/",
        )
        assert response.status_code == 302
        assert response.url == "/dashboard/"

    def test_rejects_open_redirect(self, client, user, book):
        client.force_login(user)
        response = client.get(
            reverse("PrixioApp:add_to_watchlist", args=[book.pk]) + "?next=//evil.com/",
        )
        assert response.status_code == 302
        assert "evil.com" not in response.url


class TestRemoveFromWatchlist:
    def test_removes_entry(self, client, user, watchlist):
        client.force_login(user)
        response = client.post(
            reverse("PrixioApp:remove_from_watchlist", args=[watchlist.product_id]),
        )
        assert response.status_code == 302
        assert not Watchlist.objects.filter(pk=watchlist.pk).exists()

    def test_returns_json_for_ajax(self, client, user, watchlist):
        client.force_login(user)
        response = client.post(
            reverse("PrixioApp:remove_from_watchlist", args=[watchlist.product_id]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["deleted"] == 1
        assert not Watchlist.objects.filter(pk=watchlist.pk).exists()
