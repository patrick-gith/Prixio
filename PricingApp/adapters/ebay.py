# PricingApp/adapters/ebay.py
"""
Adaptateur eBay — API Browse officielle (OAuth 2.0 client credentials).

Pourquoi eBay :
  - Couvre TOUTES les catégories : livres, électronique, jeux, vinyles, auto…
  - Donne les prix d'occasion (crucial pour la "vraie" bonne affaire)
  - API officielle, légale, stable
  - Free tier : 5 000 appels/jour — largement assez pour un portfolio

Prérequis :
  1. Créer un compte sur https://developer.ebay.com
  2. Créer une app → récupérer App ID (client_id) + Cert ID (client_secret)
  3. Mettre dans .env :
       EBAY_CLIENT_ID=xxx
       EBAY_CLIENT_SECRET=yyy
       EBAY_MARKETPLACE_ID=EBAY_FR    # EBAY_FR, EBAY_DE, EBAY_US, EBAY_GB…
"""
from __future__ import annotations

import base64
import logging
import os
import threading
import time
from decimal import Decimal, InvalidOperation
from typing import Final

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .base import Adapter, FetchedPrice

logger = logging.getLogger(__name__)


# Marketplace ID eBay par région. La devise et la langue des résultats
# sont imposées par ce paramètre.
MARKETPLACE_BY_REGION: Final[dict[str, str]] = {
    "US": "EBAY_US",
    "GB": "EBAY_GB",
    "DE": "EBAY_DE",
    "FR": "EBAY_FR",
    "IT": "EBAY_IT",
    "ES": "EBAY_ES",
    "AU": "EBAY_AU",
    "CA": "EBAY_CA",
    "IE": "EBAY_IE",
}


class _TokenCache:
    """
    Cache de token OAuth en mémoire, thread-safe.

    eBay renvoie un access_token valable ~2 h. On le réutilise jusqu'à
    60 s avant expiration, puis on le rafraîchit. Évite de faire un appel
    OAuth à chaque requête (économie de quota et latence).
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._token: str | None = None
        self._expires_at: float = 0.0

    def get(self, fetcher) -> str | None:
        with self._lock:
            now = time.time()
            if self._token and now < self._expires_at - 60:
                return self._token
            token, ttl = fetcher()
            if not token:
                return None
            self._token = token
            self._expires_at = now + ttl
            return token


# Cache partagé entre toutes les instances (une seule app eBay, un seul token)
_TOKEN_CACHE = _TokenCache()


class EbayAdapter(Adapter):
    """
    Récupère le prix le plus bas d'un produit sur eBay, pour une région.

    Stratégie :
      - On cherche par `gtin` si le produit en a un (le plus fiable).
      - Sinon on retombe sur le titre (moins précis, plus de bruit).
      - On prend l'offre la moins chère en achat immédiat (pas d'enchères).
    """

    key = "ebay"
    source_name = "eBay"
    supported_types = ["book", "electronics", "game"]

    OAUTH_URL = "https://api.ebay.com/identity/v1/oauth2/token"
    BROWSE_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"
    DEFAULT_TIMEOUT = 8
    PAGE_LIMIT = 5

    def __init__(
        self,
        region: str = "FR",
        client_id: str | None = None,
        client_secret: str | None = None,
        marketplace_id: str | None = None,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        self.region = region.upper()
        self.client_id = client_id or os.environ.get("EBAY_CLIENT_ID", "")
        self.client_secret = client_secret or os.environ.get("EBAY_CLIENT_SECRET", "")
        self.marketplace_id = (
            marketplace_id
            or os.environ.get("EBAY_MARKETPLACE_ID")
            or MARKETPLACE_BY_REGION.get(self.region, "EBAY_US")
        )
        self.timeout = timeout
        self._session = self._build_session()

    # ------------------------------------------------------------------
    # Session HTTP
    # ------------------------------------------------------------------
    @staticmethod
    def _build_session() -> requests.Session:
        session = requests.Session()
        retry = Retry(
            total=3,
            connect=3,
            read=2,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset(["GET", "POST"]),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        return session

    # ------------------------------------------------------------------
    # OAuth 2.0 — client credentials
    # ------------------------------------------------------------------
    def _fetch_token(self) -> tuple[str | None, int]:
        """Appel OAuth. Retourne (token, ttl_secondes)."""
        if not self.client_id or not self.client_secret:
            logger.warning(
                "eBay adapter: EBAY_CLIENT_ID/EBAY_CLIENT_SECRET manquants.",
            )
            return None, 0

        basic = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()

        try:
            r = self._session.post(
                self.OAUTH_URL,
                headers={
                    "Authorization": f"Basic {basic}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={
                    "grant_type": "client_credentials",
                    "scope": "https://api.ebay.com/oauth/api_scope",
                },
                timeout=(3.05, self.timeout),
            )
            r.raise_for_status()
            payload = r.json()
            return payload.get("access_token"), int(payload.get("expires_in", 7200))
        except (requests.RequestException, ValueError) as exc:
            logger.warning("eBay OAuth failed: %s", exc)
            return None, 0

    def _get_token(self) -> str | None:
        return _TOKEN_CACHE.get(self._fetch_token)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _build_query(product) -> str:
        """
        Construit la requête eBay.

        Priorité :
          1. GTIN si disponible (le plus fiable)
          2. Sinon titre tronqué (eBay n'aime pas les requêtes > 100 caractères)
        """
        attrs = getattr(product, "attributes", {}) or {}
        gtin = attrs.get("gtin") or attrs.get("ean") or attrs.get("upc")
        if gtin:
            return f"gtin:{gtin}"

        title = (getattr(product, "title", "") or "").strip()
        # eBay coupe au-delà de ~100 caractères
        return title[:100]

    # ------------------------------------------------------------------
    # Fetch
    # ------------------------------------------------------------------
    def fetch(self, product) -> FetchedPrice | None:
        token = self._get_token()
        if not token:
            return None

        query = self._build_query(product)
        if not query:
            return None

        params = {
            "q": query,
            "limit": self.PAGE_LIMIT,
            "filter": "buyingOptions:{FIXED_PRICE}",  # pas d'enchères
            "sort": "price",                          # du moins cher au plus cher
        }

        try:
            r = self._session.get(
                self.BROWSE_URL,
                params=params,
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-EBAY-C-MARKETPLACE-ID": self.marketplace_id,
                    "Accept": "application/json",
                },
                timeout=(3.05, self.timeout),
            )
            r.raise_for_status()
            data = r.json()
        except requests.RequestException as exc:
            logger.warning("eBay fetch failed for '%s': %s", query, exc)
            return None
        except ValueError as exc:
            logger.warning("eBay returned invalid JSON for '%s': %s", query, exc)
            return None

        return self._pick_best_offer(data.get("itemSummaries") or [])

    # ------------------------------------------------------------------
    # Sélection de la meilleure offre
    # ------------------------------------------------------------------
    def _pick_best_offer(self, items: list[dict]) -> FetchedPrice | None:
        best: FetchedPrice | None = None
        best_value: Decimal | None = None

        for item in items:
            price_data = item.get("price") or {}
            amount = price_data.get("value")
            currency = price_data.get("currency")
            if amount is None or not currency:
                continue

            try:
                price = Decimal(str(amount))
            except (InvalidOperation, ValueError):
                continue

            # Prix total = article + livraison (crucial pour comparer)
            shipping_data = (
                (item.get("shippingOptions") or [{}])[0].get("shippingCost") or {}
            )
            try:
                shipping = Decimal(str(shipping_data.get("value") or "0"))
            except (InvalidOperation, ValueError):
                shipping = Decimal("0")

            total = price + shipping
            if best_value is None or total < best_value:
                best_value = total
                best = FetchedPrice(
                    price_local=total,
                    currency=currency,
                    source_name=self.source_name,
                    adapter_key=self.key,
                    region=self.region,
                    in_stock=True,
                    url=item.get("itemWebUrl", ""),
                )

        return best