from .coingecko import CoinGeckoResolver
from .isbn import ISBNResolver
from .gtin import GTINResolver

RESOLVERS = [
    CoinGeckoResolver(),
    ISBNResolver(),
    GTINResolver(),
]


def resolve(raw: str):
    if not raw or not raw.strip():
        return None
    for resolver in RESOLVERS:
        if resolver.can_handle(raw):
            result = resolver.resolve(raw)
            if result:
                return result
    return None
