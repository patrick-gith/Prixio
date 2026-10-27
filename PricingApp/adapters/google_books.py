# PricingApp/adapters/google_books.py
"""
Adaptateur Google Books — supporte plusieurs régions via le paramètre `country`.

API : https://developers.google.com/books/docs/v1/using

Google Books n'expose pas systématiquement de prix (`saleInfo` peut être
vide pour beaucoup de livres). Dans ce cas on retourne `None` proprement
afin que le collecteur essaie d'autres sources.
"""
from __future__ import annotations

import logging
import re
from decimal import Decimal, InvalidOperation
from typing import Final

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .base import Adapter, FetchedPrice

logger = logging.getLogger(__name__)


# Pays officiellement supportés par Google Books (`country` param).
# Doit rester une liste blanche : un code inconnu fait retomber l'API en US.
SUPPORTED_COUNTRIES: Final[frozenset[str]] = frozenset({
    "US", "GB", "DE", "FR", "IT", "ES", "NL", "JP",
    "CA", "AU", "BR", "IN", "MX", "KR",
})


class GoogleBooksAdapter(Adapter):
    """
    Récupère le prix public d'un livre à partir de son ISBN.

    Priorité de lecture du prix :
      1. retailPrice (ce que le client paie réellement)
      2. listPrice   (prix éditeur, souvent plus élevé)
      3. FREE        (livres gratuits — prix à 0)

    Supporte plusieurs régions via le paramètre `country`, qui influence
    la devise et les prix affichés côté Google.
    """

    key = "google_books"
    source_name = "Google Books"
    supported_types = ["book"]

    API_URL = "https://www.googleapis.com/books/v1/volumes"
    DEFAULT_TIMEOUT = 8

    # ------------------------------------------------------------------
    # Init
    # ------------------------------------------------------------------
    def __init__(
        self,
        region: str = "US",
        country: str | None = None,
        api_key: str | None = None,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        """
        region  : code utilisé côté Source (ex. "FR", "DE") — sert au stockage.
        country : code pays passé à Google Books. Par défaut = region si
                  supporté, sinon US. Permet de séparer le stockage de la
                  requête (utile si tu veux stocker tout en "WORLD" mais
                  interroger en "FR").
        api_key : optionnel, augmente le quota (sinon Google limite à ~1000/j).
        """
        self.region = region.upper()
        candidate = (country or self.region).upper()
        self.country = candidate if candidate in SUPPORTED_COUNTRIES else "US"
        self.api_key = api_key
        self.timeout = timeout
        self._session = self._build_session()

    # ------------------------------------------------------------------
    # Session HTTP avec retry
    # ------------------------------------------------------------------
    @staticmethod
    def _build_session() -> requests.Session:
        session = requests.Session()
        retry = Retry(
            total=3,
            connect=3,
            read=2,
            backoff_factor=0.5,                      # 0.5s → 1s → 2s
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset(["GET"]),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _clean_isbn(raw: str) -> str:
        """Retire tirets, espaces et tout caractère non ISBN."""
        return re.sub(r"[^0-9Xx]", "", raw or "").upper()

    @staticmethod
    def _extract_url(item: dict) -> str:
        """URL de la fiche produit (page Google Books ou lien d'achat)."""
        sale = item.get("saleInfo") or {}
        access = item.get("accessInfo") or {}
        volume = item.get("volumeInfo") or {}
        return (
            sale.get("buyLink")
            or access.get("webReaderLink")
            or volume.get("infoLink", "")
            or item.get("selfLink", "")
        )

    # ------------------------------------------------------------------
    # Fetch
    # ------------------------------------------------------------------
    def fetch(self, product) -> FetchedPrice | None:
        isbn = self._clean_isbn(getattr(product, "primary_id", ""))
        if not isbn:
            return None

        params: dict[str, str | int] = {
            "q": f"isbn:{isbn}",
            "country": self.country,
            "maxResults": 5,
        }
        if self.api_key:
            params["key"] = self.api_key

        try:
            r = self._session.get(
                self.API_URL,
                params=params,
                timeout=(3.05, self.timeout),   # (connect, read)
            )
            r.raise_for_status()
            data = r.json()
        except requests.RequestException as exc:
            logger.warning(
                "Google Books fetch failed for ISBN=%s (country=%s): %s",
                isbn, self.country, exc,
            )
            return None
        except ValueError as exc:
            # JSON invalide (rare, mais peut arriver sur 5xx custom)
            logger.warning(
                "Google Books returned invalid JSON for ISBN=%s: %s", isbn, exc,
            )
            return None

        for item in (data.get("items") or []):
            offer = self._extract_offer(item)
            if offer is not None:
                return offer
        return None

    # ------------------------------------------------------------------
    # Extraction d'une offre
    # ------------------------------------------------------------------
    def _extract_offer(self, item: dict) -> FetchedPrice | None:
        sale = item.get("saleInfo") or {}
        saleability = sale.get("saleability")
        url = self._extract_url(item)

        # --- Cas 1 : livre gratuit -----------------------------------
        if saleability == "FREE":
            return FetchedPrice(
                price_local=Decimal("0"),
                currency=sale.get("retailPrice", {}).get("currencyCode", "USD"),
                source_name=self.source_name,
                adapter_key=self.key,
                region=self.region,
                in_stock=True,
                url=url,
            )

        # --- Cas 2 : pas en vente ------------------------------------
        if saleability != "FOR_SALE":
            return None

        # --- Cas 3 : en vente, on cherche un prix --------------------
        price_data = sale.get("retailPrice") or sale.get("listPrice") or {}
        amount = price_data.get("amount")
        currency = price_data.get("currencyCode")
        if amount is None or not currency:
            return None

        try:
            price = Decimal(str(amount))
        except (InvalidOperation, ValueError):
            return None

        return FetchedPrice(
            price_local=price,
            currency=currency,
            source_name=self.source_name,
            adapter_key=self.key,
            region=self.region,
            in_stock=True,
            url=url,
        )