# PricingApp/views.py
from django.shortcuts import render
from django.utils.translation import gettext as _

from .models import PricePoint, Source
from CatalogApp.models import Product


def stats(request):
    """Vue globale : combien de produits, de relevés, de sources."""
    return render(request, "PricingApp/stats.html", {
        "product_count": Product.objects.count(),
        "price_count": PricePoint.objects.count(),
        "source_count": Source.objects.filter(is_active=True).count(),
        "sources": Source.objects.filter(is_active=True),
        "title": _("Statistiques"),
    })