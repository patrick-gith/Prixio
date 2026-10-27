"""Tests des vues principales."""

import pytest
from django.urls import reverse

from PricingApp.models import Watchlist


@pytest.mark.django_db
class TestWatchlist:
    def test_add_requires_login(self, client, book):
        url = reverse("PrixioApp:add_to_watchlist", args=[book.id])
        response = client.get(url)
        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_add_creates_watchlist(self, client, user, book):
        client.force_login(user)
        url = reverse("PrixioApp:add_to_watchlist", args=[book.id])
        response = client.get(url)
        assert response.status_code == 302
        assert Watchlist.objects.filter(user=user, product=book).exists()

    def test_add_twice_shows_info_message(self, client, user, book, watchlist):
        client.force_login(user)
        url = reverse("PrixioApp:add_to_watchlist", args=[book.id])
        response = client.get(url, follow=True)
        messages = [str(m) for m in response.context["messages"]]
        assert any("déjà" in m for m in messages)

    def test_remove_works(self, client, user, book, watchlist):
        client.force_login(user)
        url = reverse("PrixioApp:remove_from_watchlist", args=[book.id])
        response = client.get(url)
        assert response.status_code == 302
        assert not Watchlist.objects.filter(user=user, product=book).exists()


@pytest.mark.django_db
class TestAuth:
    def test_register_creates_user_and_logs_in(self, client):
        url = reverse("register")
        data = {
            "username": "newuser",
            "email": "new@example.com",
            "password1": "SuperSecret123!",
            "password2": "SuperSecret123!",
        }
        response = client.post(url, data)
        assert response.status_code == 302
        assert response.url == reverse("PrixioApp:dashboard")

        from django.contrib.auth.models import User
        assert User.objects.filter(username="newuser").exists()