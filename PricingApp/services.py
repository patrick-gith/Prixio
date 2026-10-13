# PricingApp/services.py
"""
Collecte des prix multi-sources, en parallèle.

Avant : 6 adaptateurs × 1,2 s = 7,2 s par produit.
Après : max(1,2 s) ≈ 1,3 s par produit.

Utilise ThreadPoolExecutor car les appels sont I/O-bound (HTTP).
"""
from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

from django.db import transaction

from CatalogApp.models import Product
from .models import Source, PricePoint
from .adapters import get_adapters_for
from .adapters.base import FetchedPrice


logger = logging.getLogger(__name__)


# Nombre maximum d'appels HTTP simultanés.
# 4–6 est un bon compromis : assez rapide, pas de rate limit agressif.
MAX_WORKERS = 5

# Timeout global pour l'ensemble de la collecte d'un produit.
# Au-delà, on abandonne les adaptateurs encore en cours.
COLLECT_TIMEOUT_SECONDS = 15


@dataclass
class CollectResult:
    """Résultat structuré d'une collecte."""
    created: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)
    sources_used: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        return (
            f"{self.created} prix créés, {self.failed} échecs "
            f"({', '.join(self.sources_used) or 'aucune source'})"
        )


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

def _persist_price(product: Product, fetched: FetchedPrice) -> bool:
    """
    Enregistre un FetchedPrice en base. Idempotent dans la minute :
    on ne crée pas de doublon si la même source a déjà répondu dans les
    60 dernières secondes pour ce produit.
    """
    from django.utils import timezone
    from datetime import timedelta

    source, _ = Source.objects.get_or_create(
        adapter_key=fetched.adapter_key,
        region=fetched.region,
        defaults={
            "name": fetched.source_name,
            "currency": fetched.currency,
        },
    )

    # Anti-doublon : la même source + même produit dans la dernière minute
    cutoff = timezone.now() - timedelta(seconds=60)
    already = PricePoint.objects.filter(
        product=product, source=source, captured_at__gte=cutoff,
    ).exists()
    if already:
        return False

    PricePoint.objects.create(
        product=product,
        source=source,
        price_local=fetched.price_local,
        currency=fetched.currency,
        in_stock=fetched.in_stock,
    )
    return True


def _fetch_one(adapter, product: Product) -> tuple[str, FetchedPrice | None, str | None]:
    """
    Wrapper qui capture les exceptions d'un adaptateur.
    Retourne (adapter_key, FetchedPrice | None, erreur | None).
    """
    try:
        return adapter.key, adapter.fetch(product), None
    except Exception as exc:  # noqa: BLE001
        logger.exception("Adapter %s crashed", adapter.key)
        return adapter.key, None, str(exc)


# ----------------------------------------------------------------------
# API publique
# ----------------------------------------------------------------------

def collect_prices_for(product: Product) -> CollectResult:
    """
    Collecte les prix de toutes les sources qui supportent ce produit,
    en parallèle. Ne lève jamais : retourne un CollectResult même en cas
    d'échec global.

    Exemple :
        result = collect_prices_for(product)
        print(result)  # "5 prix créés, 1 échecs (ebay, google_books, ...)"
    """
    adapters = get_adapters_for(product)
    if not adapters:
        return CollectResult()

    result = CollectResult()
    futures = []

    # ThreadPoolExecutor : I/O-bound, donc parfait pour HTTP
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        for adapter in adapters:
            futures.append(pool.submit(_fetch_one, adapter, product))

        for future in as_completed(futures, timeout=COLLECT_TIMEOUT_SECONDS):
            adapter_key, fetched, error = future.result()

            if error:
                result.failed += 1
                result.errors.append(f"{adapter_key}: {error}")
                continue

            if fetched is None:
                # Pas de prix — normal (produit non vendu sur cette source)
                continue

            try:
                with transaction.atomic():
                    created = _persist_price(product, fetched)
                if created:
                    result.created += 1
                    result.sources_used.append(adapter_key)
            except Exception as exc:  # noqa: BLE001
                logger.exception("Failed to persist %s for %s", adapter_key, product)
                result.failed += 1
                result.errors.append(f"{adapter_key}: persist failed ({exc})")

    return result


# ----------------------------------------------------------------------
# Version batch — pour la commande management collect_all
# ----------------------------------------------------------------------

def collect_prices_for_many(products: list[Product]) -> dict[int, CollectResult]:
    """
    Collecte en série sur les produits, mais en parallèle sur les sources.
    À utiliser dans collect_all ; pour aller plus loin, parallélise aussi
    au niveau produits (cf. note ci-dessous).
    """
    results: dict[int, CollectResult] = {}
    for product in products:
        results[product.id] = collect_prices_for(product)
    return results