# CatalogApp/resolvers/openfoodfacts.py
import re

import requests

from .base import ResolvedProduct, Resolver


class OpenFoodFactsResolver(Resolver):
    name = "openfoodfacts"

    # L'API Open Food Facts utilise des codes-barres (EAN-13, UPC-A, etc.)
    # On valide donc la présence de 8, 12, 13 ou 14 chiffres.
    def can_handle(self, raw: str) -> bool:
        cleaned = re.sub(r"[^0-9]", "", raw)
        return len(cleaned) in (8, 12, 13, 14)

    def resolve(self, raw: str) -> ResolvedProduct | None:
        barcode = re.sub(r"[^0-9]", "", raw)
        # Endpoint officiel pour récupérer un produit par son code-barres
        url = f"https://world.openfoodfacts.org/api/v2/product/{barcode}.json"

        # Un User-Agent identifiant est recommandé (et parfois requis)
        headers = {
            "User-Agent": "Prixio/1.0 (contact@prixio.app)"
        }

        try:
            r = requests.get(url, headers=headers, timeout=8)
            if r.status_code != 200:
                return None

            data = r.json()
            if data.get("status") != 1: # status=1 signifie succès
                return None

            product = data.get("product", {})

            # On extrait les informations les plus utiles pour un catalogue
            return ResolvedProduct(
                canonical_type="food",
                primary_id=barcode,
                title=product.get("product_name", "—"),
                brand=product.get("brands", ""),
                image_url=product.get("image_url", ""),
                attributes={
                    "categories": product.get("categories", ""),
                    "quantity": product.get("quantity", ""),
                    "nutriscore": product.get("nutriscore_grade", "").upper(),
                },
            )
        except requests.RequestException:
            return None