# PricingApp/adapters/__init__.py
from .base import Adapter, FetchedPrice
from .coingecko import CoinGeckoAdapter
from .google_books import GoogleBooksAdapter
from .steam import SteamAdapter
from .ebay import EbayAdapter
from .openfoodfacts import OpenFoodFactsAdapter  # <-- Ajout

ALL_ADAPTERS = [
    CoinGeckoAdapter(),
    GoogleBooksAdapter(region="US"),
    GoogleBooksAdapter(region="FR"),
    GoogleBooksAdapter(region="DE"),
    EbayAdapter(region="FR"),
    EbayAdapter(region="DE"),
    EbayAdapter(region="US"),
    SteamAdapter(),
    OpenFoodFactsAdapter(),  # <-- Ajout
]

def get_adapters_for(product):
    return [a for a in ALL_ADAPTERS if a.supports(product)]

