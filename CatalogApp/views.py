# CatalogApp/views.py
from django.shortcuts import render
from django.utils.translation import gettext as _

from .models import Product


def product_list(request):
    """Liste publique des produits déjà résolus (utile pour la démo)."""
    products = Product.objects.all().order_by("-created_at")[:100]
    return render(request, "CatalogApp/product_list.html", {
        "products": products,
        "title": _("Tous les produits"),
    })