"""Résolution d'une ligne batch → produit canonique.

Stratégie :
  1. Si ISBN/GTIN/EAN présent → résolution directe (100%)
  2. Sinon fuzzy matching sur la désignation via rapidfuzz
  3. Seuil 0.82 → matched ; 0.65-0.82 → ambiguous ; <0.65 → not_found
"""
import re
from dataclasses import dataclass

from rapidfuzz import fuzz, process

from CatalogApp.models import Product
from CatalogApp.services import get_or_create_product


IDENTIFIER_PATTERNS = {
    "isbn": re.compile(r"^\d{13}$|^\d{9}[\dX]$"),
    "gtin": re.compile(r"^\d{8}$|^\d{12,14}$"),
}

MATCH_THRESHOLD = 0.82
AMBIGUOUS_THRESHOLD = 0.65


@dataclass
class MatchResult:
    product: Product | None
    confidence: float
    status: str           # matched | ambiguous | not_found
    candidates: list      # top 3 si ambiguous


def match_line(designation: str, reference: str = "") -> MatchResult:
    designation = (designation or "").strip()
    reference = (reference or "").strip()

    # 1. Identifiant direct
    for raw in (reference, designation):
        clean = re.sub(r"[^0-9X]", "", raw.upper())
        for kind, pattern in IDENTIFIER_PATTERNS.items():
            if pattern.match(clean):
                product = get_or_create_product(clean)
                if product:
                    return MatchResult(product, 1.0, "matched", [])

    if not designation:
        return MatchResult(None, 0.0, "not_found", [])

    # 2. Fuzzy matching
    candidates = _fuzzy_search(designation, limit=5)
    if not candidates:
        return MatchResult(None, 0.0, "not_found", [])

    top = candidates[0]
    score = top["score"] / 100.0

    if score >= MATCH_THRESHOLD:
        return MatchResult(top["product"], score, "matched", candidates[:3])
    if score >= AMBIGUOUS_THRESHOLD:
        return MatchResult(None, score, "ambiguous", candidates[:3])
    return MatchResult(None, score, "not_found", candidates[:3])


def _fuzzy_search(query: str, limit: int = 5) -> list[dict]:
    """Cherche les produits les plus proches par désignation."""
    products = Product.objects.filter(
        title__isnull=False,
    ).exclude(title="").only("id", "title", "primary_id", "canonical_type")

    if not products.exists():
        return []

    choices = {p.id: p.title for p in products}
    matches = process.extract(
        query, choices,
        scorer=fuzz.WRatio,
        limit=limit,
        score_cutoff=50,
    )

    results = []
    for title, score, pid in matches:
        try:
            product = Product.objects.get(pk=pid)
            results.append({
                "product": product,
                "title": product.title,
                "primary_id": product.primary_id,
                "type": product.canonical_type,
                "score": score,
            })
        except Product.DoesNotExist:
            continue
    return results