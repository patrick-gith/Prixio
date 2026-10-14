
# PricingApp/adapters/openfoodfacts.py

import re
from decimal import Decimal, InvalidOperation

import requests

from .base import Adapter, FetchedPrice


class OpenFoodFactsAdapter(Adapter):
    key = "openfoodfacts"
    source_name = "Open Food Facts"
    supported_types = ["food"]

    API_URL = "https://world.openfoodfacts.org/api/v3/product/{}.json"

    def fetch(self, product) -> FetchedPrice | None:
        barcode = getattr(product, "primary_id", None)

        if not barcode:
            return None

        url = self.API_URL.format(barcode)
        headers = {
            "User-Agent": "Prixio/1.0 (contact@prixio.app)",
            "Accept": "application/json",
        }

        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=8,
            )
            response.raise_for_status()
            data = response.json()

        except (
            requests.RequestException,
            ValueError,
        ):
            return None

        if data.get("status") != 1:
            return None

        product_data = data.get("product") or {}

        # Open Food Facts ne garantit pas la présence
        # d'un prix commercial exploitable.
        raw_price = product_data.get("price")

        if raw_price is None or isinstance(raw_price, bool):
            return None

        try:
            # Accepte les nombres et les chaînes comme "3.50".
            # N'interprète pas arbitrairement les séparateurs
            # décimaux ambigus.
            if isinstance(raw_price, (int, float, Decimal)):
                price = Decimal(str(raw_price))
            else:
                cleaned = re.sub(
                    r"\s+",
                    "",
                    str(raw_price),
                )

                if not re.fullmatch(
                    r"\d+(?:\.\d{1,4})?",
                    cleaned,
                ):
                    return None

                price = Decimal(cleaned)

            if not price.is_finite() or price <= 0:
                return None

        except (InvalidOperation, ValueError, TypeError):
            return None

        # Ne pas supposer que la devise est l'euro.
        currency = (
            product_data.get("price_currency")
            or product_data.get("currency")
        )

        if not isinstance(currency, str):
            return None

        currency = currency.upper().strip()

        if not re.fullmatch(r"[A-Z]{3}", currency):
            return None

        product_url = (
            product_data.get("url")
            or f"https://world.openfoodfacts.org/product/{barcode}"
        )

        return FetchedPrice(
            price_local=price,
            currency=currency,
            source_name=self.source_name,
            adapter_key=self.key,
            region="WORLD",
            in_stock=True,
            url=product_url,
        )
