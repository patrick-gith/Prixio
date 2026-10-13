from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.http import HttpResponse
from django.utils.text import slugify
from django.conf import settings
from .pdf import render_purchase_order_pdf
from .engines.forecast import procurement_signal
from CatalogApp.models import Product
from django.contrib import messages
from .models import PricePoint, Source, CompetitorListing, PurchaseIntent
from .engines.comparison import market_position
from django.utils import translation


def stats(request):
    return render(request, "PricingApp/stats.html", {
        "product_count": Product.objects.count(),
        "price_count": PricePoint.objects.count(),
        "source_count": Source.objects.filter(is_active=True).count(),
        "sources": Source.objects.filter(is_active=True),
        "title": _("Statistiques"),
    })


@login_required
def competitor_dashboard(request):
    """Mode B — mes produits vs le marché."""
    listings = (
        CompetitorListing.objects
        .filter(user=request.user)
        .select_related("product")
    )
    rows = []
    for listing in listings:
        result = market_position(
            listing.product, listing.my_price,
            listing.my_currency, listing.region,
        )
        rows.append({"listing": listing, "result": result})

    return render(request, "PricingApp/competitor.html", {
        "rows": rows,
        "title": _("Veille concurrentielle"),
    })


@login_required
def procurement_dashboard(request):
    """Mode C — intentions d'achat + signaux."""
    intents = (
        PurchaseIntent.objects
        .filter(user=request.user, status="pending")
        .select_related("product")
    )
    rows = []
    for intent in intents:
        profile = getattr(request.user, "prixio_profile", None)
        currency = profile.currency if profile else "EUR"
        result = procurement_signal(
            intent.product, intent.quantity, intent.deadline, currency,
        )
        rows.append({"intent": intent, "result": result})

    return render(request, "PricingApp/procurement.html", {
        "rows": rows,
        "title": _("Assistant achats"),
    })




@login_required
def purchase_order_pdf(request, intent_id: int):
    """Génère et renvoie le PDF du bon de commande."""
    intent = get_object_or_404(
        PurchaseIntent,
        pk=intent_id,
        user=request.user,   # sécurité : un user ne voit que ses intentions
    )

    profile = getattr(request.user, "prixio_profile", None)
    currency = profile.currency if profile else settings.BASE_CURRENCY

    signal = procurement_signal(
        intent.product, intent.quantity, intent.deadline, currency,
    )
    if not signal.get("has_data"):
        messages.error(
            request,
            _("Pas assez de données pour générer un bon de commande pour « %(t)s ».")
            % {"t": intent.product.title},
        )
        return redirect("PricingApp:procurement")

    pdf_bytes = render_purchase_order_pdf(
        intent=intent, signal=signal, user_profile=profile,
        language=translation.get_language(),
    )

    filename = (
        f"bon-commande-{slugify(intent.product.title)[:40]}-"
        f"{intent.id}.pdf"
    )
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response