from decimal import Decimal
import requests
from .base import Adapter, FetchedPrice


class CoinGeckoAdapter(Adapter):
    key = "coingecko"
    source_name = "CoinGecko"
    region = "WORLD"
    currency = "EUR"
    supported_types = ["crypto"]

    def fetch(self, product) -> FetchedPrice | None:
        try:
            r = requests.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={"ids": product.primary_id, "vs_currencies": "eur,usd"},
                timeout=8,
            )
            r.raise_for_status()
            data = r.json().get(product.primary_id, {})
            if "eur" not in data:
                return None
            return FetchedPrice(
                price_local=Decimal(str(data["eur"])),
                currency="EUR",
                source_name=self.source_name,
                adapter_key=self.key,
                region=self.region,
            )
        except requests.RequestException:
            return None
