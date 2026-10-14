# CatalogApp/resolvers/__init__.py
from .base import Resolver, ResolvedProduct
from .isbn import ISBNResolver
from .gtin import GTINResolver
from .coingecko import CoinGeckoResolver
from .openfoodfacts import OpenFoodFactsResolver  # <-- Ajout

ALL_RESOLVERS = [
    ISBNResolver(),
    OpenFoodFactsResolver(),  # <-- Ajout
    GTINResolver(),
    CoinGeckoResolver(),   
]

def resolve(raw: str) -> ResolvedProduct | None:
    for resolver in ALL_RESOLVERS:
        if resolver.can_handle(raw):
            result = resolver.resolve(raw)
            if result:
                return result
    return None



