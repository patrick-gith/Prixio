from .google_books import GoogleBooksAdapter
from .coingecko import CoinGeckoAdapter

ADAPTERS = [
    GoogleBooksAdapter(),
    CoinGeckoAdapter(),
]


def get_adapters_for(product):
    return [a for a in ADAPTERS if a.supports(product)]
