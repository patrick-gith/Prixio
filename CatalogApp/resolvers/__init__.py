# CatalogApp/resolvers/__init__.py
from .base import ResolvedProduct, Resolver
from .coingecko import CoinGeckoResolver
from .gtin import GTINResolver
from .isbn import ISBNResolver
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



