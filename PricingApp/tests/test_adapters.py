"""Tests des adaptateurs avec réponses HTTP mockées."""
from decimal import Decimal
from unittest.mock import patch, Mock

import pytest

from CatalogApp.models import Product
from PricingApp.adapters.google_books import GoogleBooksAdapter


@pytest.mark.django_db
class TestGoogleBooksAdapter:
    def test_clean_isbn(self):
        adapter = GoogleBooksAdapter(region="FR")
        assert adapter._clean_isbn("978-2-07-040850-4") == "9782070408504"
        assert adapter._clean_isbn(" 9782070408504 ") == "9782070408504"

    def test_country_fallback(self):
        """Un code pays non supporté retombe sur US."""
        adapter = GoogleBooksAdapter(region="XX")
        assert adapter.country == "US"

    def test_country_respected(self):
        adapter = GoogleBooksAdapter(region="FR")
        assert adapter.country == "FR"

    def test_fetch_extracts_retail_price(self, book):
        """Doit préférer retailPrice à listPrice."""
        adapter = GoogleBooksAdapter(region="FR")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "items": [{
                "saleInfo": {
                    "saleability": "FOR_SALE",
                    "retailPrice": {"amount": 9.20, "currencyCode": "EUR"},
                    "listPrice": {"amount": 12.40, "currencyCode": "EUR"},
                },
                "volumeInfo": {"infoLink": "https://books.google.fr/..."},
            }],
        }

        with patch.object(adapter._session, "get", return_value=mock_response):
            result = adapter.fetch(book)

        assert result is not None
        assert result.price_local == Decimal("9.20")
        assert result.currency == "EUR"
        assert result.region == "FR"

    def test_fetch_returns_none_when_not_for_sale(self, book):
        adapter = GoogleBooksAdapter(region="FR")
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "items": [{"saleInfo": {"saleability": "NOT_FOR_SALE"}}],
        }

        with patch.object(adapter._session, "get", return_value=mock_response):
            result = adapter.fetch(book)

        assert result is None

    def test_fetch_handles_network_error(self, book):
        import requests
        adapter = GoogleBooksAdapter(region="FR")

        with patch.object(adapter._session, "get", side_effect=requests.RequestException("boom")):
            result = adapter.fetch(book)

        assert result is None

    def test_free_book(self, book):
        adapter = GoogleBooksAdapter(region="FR")
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "items": [{
                "saleInfo": {"saleability": "FREE"},
            }],
        }

        with patch.object(adapter._session, "get", return_value=mock_response):
            result = adapter.fetch(book)

        assert result is not None
        assert result.price_local == Decimal("0")