from decimal import Decimal
import requests
from .base import Adapter, FetchedPrice


class GoogleBooksAdapter(Adapter):
    key = "google_books"
    source_name = "Google Books"
    region = "US"
    currency = "USD"
    supported_types = ["book"]

    def fetch(self, product) -> FetchedPrice | None:
        try:
            r = requests.get(
                "https://www.googleapis.com/books/v1/volumes",
                params={"q": f"isbn:{product.primary_id}"},
                timeout=8,
            )
            r.raise_for_status()
            items = r.json().get("items", [])
            for item in items:
                sale = item.get("saleInfo", {})
                if sale.get("saleability") == "FOR_SALE":
                    amount = sale.get("listPrice", {}).get("amount")
                    currency = sale.get("listPrice", {}).get("currencyCode", "USD")
                    if amount:
                        return FetchedPrice(
                            price_local=Decimal(str(amount)),
                            currency=currency,
                            source_name=self.source_name,
                            adapter_key=self.key,
                            region=self.region,
                        )
            return None
        except requests.RequestException:
            return None
