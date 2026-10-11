from dataclasses import dataclass
from decimal import Decimal


@dataclass
class FetchedPrice:
    price_local: Decimal
    currency: str
    source_name: str
    adapter_key: str
    region: str
    in_stock: bool = True
    url: str = ""


class Adapter:
    key = "base"
    source_name = "Source"
    region = "WORLD"
    currency = "EUR"
    supported_types: list[str] = []

    def supports(self, product) -> bool:
        return product.canonical_type in self.supported_types

    def fetch(self, product) -> FetchedPrice | None:
        raise NotImplementedError
