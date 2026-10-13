"""
Récupère les coordonnées d'un vendeur à partir d'une offre.
Utilise un cache DB pour éviter les appels répétés.
"""
import logging
from dataclasses import dataclass, asdict

import requests
from django.core.cache import cache

logger = logging.getLogger(__name__)


CACHE_TTL = 60 * 60 * 24 * 30  # 30 jours


@dataclass
class SupplierContact:
    name: str = ""
    email: str = ""
    phone: str = ""
    address: str = ""
    country: str = ""
    website: str = ""
    verified: bool = False


# Contacts pré-remplis pour les sources connues
KNOWN_SUPPLIERS = {
    "amazon":       {"name": "Amazon Business", "website": "https://business.amazon.fr",
                     "email": "contact@amazon.fr", "country": "FR"},
    "ebay":         {"name": "eBay", "website": "https://www.ebay.fr",
                     "email": "", "country": "FR"},
    "google_books": {"name": "Google Books", "website": "https://books.google.fr",
                     "email": "", "country": "FR"},
    "steam":        {"name": "Steam", "website": "https://store.steampowered.com",
                     "email": "support@steampowered.com", "country": "US"},
    "coingecko":    {"name": "CoinGecko", "website": "https://www.coingecko.com",
                     "email": "hello@coingecko.com", "country": "WORLD"},
}


def find_supplier_for_offer(source_name: str, region: str, product) -> dict:
    """
    Retourne les coordonnées d'un vendeur. Essaie dans l'ordre :
      1. Cache
      2. Table KNOWN_SUPPLIERS
      3. Google Places API (si clé configurée)
      4. Fallback : vides
    """
    key = f"supplier:{source_name}:{region}".lower()
    cached = cache.get(key)
    if cached:
        return cached

    # 1. Connus
    base_key = source_name.lower().replace(" ", "_").split("_")[0]
    known = KNOWN_SUPPLIERS.get(base_key)
    if known:
        contact = SupplierContact(**known).__dict__
        contact["region"] = region
        cache.set(key, contact, CACHE_TTL)
        return contact

    # 2. Google Places (optionnel)
    gkey = _try_google_places(source_name, region)
    if gkey:
        cache.set(key, gkey, CACHE_TTL)
        return gkey

    # 3. Fallback
    fallback = asdict(SupplierContact(
        name=source_name, country=region,
    ))
    return fallback


def _try_google_places(name: str, region: str) -> dict | None:
    """Recherche l'adresse/téléphone via Google Places. Retourne None si pas de clé."""
    import os
    api_key = os.environ.get("GOOGLE_PLACES_API_KEY")
    if not api_key or not name:
        return None

    try:
        r = requests.get(
            "https://maps.googleapis.com/maps/api/place/findplacefromtext/json",
            params={
                "input": f"{name} {region}",
                "inputtype": "textquery",
                "fields": "name,formatted_address,formatted_phone_number,website",
                "key": api_key,
            },
            timeout=5,
        )
        r.raise_for_status()
        candidates = r.json().get("candidates") or []
        if not candidates:
            return None
        c = candidates[0]
        return asdict(SupplierContact(
            name=c.get("name", name),
            address=c.get("formatted_address", ""),
            phone=c.get("formatted_phone_number", ""),
            website=c.get("website", ""),
            country=region,
            verified=True,
        ))
    except Exception as exc:
        logger.debug("Google Places lookup failed for %s: %s", name, exc)
        return None