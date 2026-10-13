# PricingApp/pdf.py
"""
Génération PDF du bon de commande (Mode C — Procurement).

Utilise WeasyPrint : HTML + CSS → PDF. Avantages :
  - On garde le design system (polices, couleurs) du site
  - Pas de duplication de mise en page
  - Support des images, tableaux, en-têtes/pieds de page CSS
"""
from __future__ import annotations

import logging
from decimal import Decimal

from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone, translation

logger = logging.getLogger(__name__)


def render_purchase_order_pdf(
    intent,
    signal: dict,
    user_profile=None,
    language: str | None = None,
    company_name: str | None = None,
    company_email: str | None = None,
) -> bytes:
    """
    Retourne les octets du PDF du bon de commande.

    Éléments inclus :
      - En-tête : nom de l'entreprise, date d'émission
      - Référence unique : PO-YYYYMMDD-<id>
      - Produit, quantité, prix unitaire actuel, prix prévisionnel
      - Signal BUY_NOW / WAIT / NEUTRAL + économie estimée
      - Pied de page : mention "Prixio", pagination, conditions
    """
    # Import tardif : WeasyPrint est lent au boot (charge Pango, Cairo…)
    from weasyprint import HTML, CSS

    language = language or translation.get_language() or "fr"

    with translation.override(language):
        context = _build_context(
            intent=intent,
            signal=signal,
            user_profile=user_profile,
            company_name=company_name,
            company_email=company_email,
            language=language,
        )

        html_string = render_to_string(
            "PricingApp/pdf/purchase_order.html", context,
        )
        css_string = render_to_string(
            "PricingApp/pdf/purchase_order.css", context,
        )

        pdf_bytes = HTML(string=html_string).write_pdf(
            stylesheets=[CSS(string=css_string)],
            presentational_hints=True,
        )

    return pdf_bytes


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

def _build_context(
    intent,
    signal: dict,
    user_profile,
    company_name: str | None,
    company_email: str | None,
    language: str = "fr",
) -> dict:
    currency = signal.get("currency") or (
        user_profile.currency if user_profile else settings.BASE_CURRENCY
    )
    quantity = intent.quantity

    current_price = Decimal(str(signal.get("current_price", 0)))
    forecast_price = Decimal(str(signal.get("forecast_price", 0)))
    delta_pct = float(signal.get("delta_pct", 0))

    # Prix de référence : selon le signal, on retient l'actuel ou le prévisionnel
    if signal.get("signal") == "WAIT":
        reference_price = forecast_price
    else:
        reference_price = current_price

    total = (reference_price * quantity).quantize(Decimal("0.01"))
    total_current = (current_price * quantity).quantize(Decimal("0.01"))
    total_saving = abs((total_current - total)).quantize(Decimal("0.01"))

    days_ahead = int(signal.get("days_ahead", 0))

    return {
        "company_name": company_name or settings.COMPANY_NAME,
        "company_email": company_email or settings.COMPANY_EMAIL,
        "reference": _build_reference(intent),
        "issued_at": timezone.now(),
        "buyer_username": intent.user.username,
        "buyer_email": intent.user.email,
        "product": intent.product,
        "quantity": quantity,
        "deadline": intent.deadline,
        "days_ahead": days_ahead,
        "currency": currency,
        "current_price": current_price,
        "forecast_price": forecast_price,
        "reference_price": reference_price,
        "delta_pct": delta_pct,
        "total": total,
        "total_current": total_current,
        "total_saving": total_saving,
        "signal": signal.get("signal", "NEUTRAL"),
        "signal_label": _signal_label(signal.get("signal", "NEUTRAL"), language),
        "region": intent.region,
        "language_code": language,
    }


def _build_reference(intent) -> str:
    """Référence unique : PO-YYYYMMDD-<id>."""
    return f"PO-{timezone.now():%Y%m%d}-{intent.id:05d}"


def _signal_label(signal: str, language: str = "fr") -> str:
    """Libellé traduit du signal, selon la langue active."""
    labels = {
        "fr": {
            "WAIT": "ATTENDRE",
            "BUY_NOW": "ACHETER MAINTENANT",
            "NEUTRAL": "PRIX STABLE",
        },
        "en": {
            "WAIT": "WAIT",
            "BUY_NOW": "BUY NOW",
            "NEUTRAL": "PRICE STABLE",
        },
    }
    return labels.get(language, labels["fr"]).get(signal, "—")