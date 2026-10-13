# PricingApp/api.py
"""
API JSON en lecture seule.

Endpoints :
  GET /api/v1/analyze/?identifier=<isbn|gtin|coingecko>
  GET /api/v1/product/<int:product_id>/
  GET /api/v1/watchlist/                (authentifié)

Authentification :
  - Session (utilisateur connecté)
  - Header "X-API-Key: <key>" pour les intégrations serveur
"""
from __future__ import annotations

import hashlib
import hmac
import os

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt

from CatalogApp.models import Product
from CatalogApp.services import get_or_create_product
from PricingApp.analysis import analyze_product
from PricingApp.services import collect_prices_for


API_KEY = os.environ.get("PRIXIO_API_KEY", "")


def _check_api_key(request) -> bool:
    """Retourne True si la requête est autorisée."""
    # Utilisateur connecté → OK
    if request.user.is_authenticated:
        return True

    # Header X-API-Key
    provided = request.headers.get("X-API-Key", "")
    if not API_KEY or not provided:
        return False

    # Comparaison constant-time pour éviter le timing attack
    return hmac.compare_digest(provided, API_KEY)


def _error(message: str, status: int = 400) -> JsonResponse:
    return JsonResponse({"ok": False, "error": message}, status=status)


@require_GET
def api_analyze(request):
    """
    Analyse un produit par identifiant.

    Exemple :
        GET /api/v1/analyze/?identifier=9782070408504
        GET /api/v1/analyze/?identifier=bitcoin
    """
    if not _check_api_key(request):
        return _error("API key required.", status=401)

    identifier = (request.GET.get("identifier") or "").strip()
    if not identifier:
        return _error("Paramètre 'identifier' requis.")

    # Rate limit simple : max 30 requêtes / min / IP
    if not _rate_limit_ok(request, key="analyze", limit=30, window=60):
        return _error("Trop de requêtes. Réessayez dans une minute.", status=429)

    product = get_or_create_product(identifier)
    if not product:
        return _error(f"Produit introuvable pour « {identifier} ».", status=404)

    collect_prices_for(product)
    analysis = analyze_product(product)

    return JsonResponse({
        "ok": True,
        "product": _serialize_product(product),
        "analysis": _serialize_analysis(analysis),
    })


@require_GET
def api_product(request, product_id: int):
    """Analyse un produit par son ID Prixio."""
    if not _check_api_key(request):
        return _error("API key required.", status=401)

    try:
        product = Product.objects.get(pk=product_id)
    except Product.DoesNotExist:
        return _error("Produit inconnu.", status=404)

    analysis = analyze_product(product)
    return JsonResponse({
        "ok": True,
        "product": _serialize_product(product),
        "analysis": _serialize_analysis(analysis),
    })


# ----------------------------------------------------------------------
# Sérialisation
# ----------------------------------------------------------------------

def _serialize_product(product) -> dict:
    return {
        "id": product.id,
        "canonical_type": product.canonical_type,
        "primary_id": product.primary_id,
        "title": product.title,
        "brand": product.brand,
        "image_url": product.image_url,
    }


def _serialize_analysis(analysis: dict) -> dict:
    if not analysis.get("has_data"):
        return {"has_data": False}

    return {
        "has_data": True,
        "score": analysis.get("score"),
        "label": analysis.get("label"),
        "current_price": analysis.get("current_price"),
        "currency": analysis.get("currency"),
        "baseline": {
            "median": analysis.get("baseline", {}).get("median"),
            "p10": analysis.get("baseline", {}).get("p10"),
            "p90": analysis.get("baseline", {}).get("p90"),
            "volatility": analysis.get("baseline", {}).get("volatility"),
            "count": analysis.get("baseline", {}).get("count"),
        },
        "deviation_pct": analysis.get("deviation_pct"),
        "best_offer": analysis.get("best_offer"),
        "history": analysis.get("history", [])[:30],
    }


# ----------------------------------------------------------------------
# Rate limit basé sur le cache (Django cache framework)
# ----------------------------------------------------------------------

def _rate_limit_ok(request, key: str, limit: int, window: int) -> bool:
    from django.core.cache import cache
    ip = request.META.get("REMOTE_ADDR", "unknown")
    bucket = f"rl:{key}:{ip}:{int(__import__('time').time() // window)}"
    count = cache.get(bucket, 0)
    if count >= limit:
        return False
    cache.set(bucket, count + 1, timeout=window)
    return True