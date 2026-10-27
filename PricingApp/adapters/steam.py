"""Prix Steam par région (API publique, pas de clé)."""
from decimal import Decimal

import requests

from .base import Adapter, FetchedPrice


class SteamAdapter(Adapter):
    key = "steam"
    source_name = "Steam"
    region = "WORLD"
    currency = "EUR"
    supported_types = ["game"]

    # cc = code pays Steam (fr, de, us, gb…)
    REGION_CC = {"FR": "fr", "DE": "de", "US": "us", "GB": "gb", "JP": "jp"}

    def fetch(self, product) -> FetchedPrice | None:
        app_id = product.primary_id
        cc = self.REGION_CC.get(self.region, "fr")
        try:
            r = requests.get(
                "https://store.steampowered.com/api/appdetails",
                params={"appids": app_id, "cc": cc, "filters": "price_overview"},
                timeout=8,
            )
            r.raise_for_status()
            data = r.json().get(str(app_id), {}).get("data", {})
            price = data.get("price_overview")
            if not price:
                return None
            return FetchedPrice(
                price_local=Decimal(str(price["final"] / 100)),
                currency=price["currency"],
                source_name=self.source_name,
                adapter_key=self.key,
                region=self.region,
            )
        except requests.RequestException:
            return None