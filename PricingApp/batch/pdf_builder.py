"""Génère UN PDF unique contenant tout le dossier commande."""
from decimal import Decimal

from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone


def build_batch_pdf(job) -> bytes:
    """Retourne les octets du PDF batch."""
    from weasyprint import CSS, HTML

    context = _build_context(job)
    html = render_to_string("PricingApp/pdf/batch_report.html", context)
    css = render_to_string("PricingApp/pdf/batch_report.css", context)

    return HTML(string=html).write_pdf(
        stylesheets=[CSS(string=css)],
        presentational_hints=True,
    )


def _build_context(job) -> dict:
    lines = list(job.lines.select_related("product").all())
    resolved = [l for l in lines if l.product_id]

    # Regroupe par fournisseur pour le récap
    by_supplier: dict = {}
    for line in resolved:
        for offer in line.best_offers:
            if "source" not in offer:
                continue
            key = offer["source"]
            by_supplier.setdefault(key, {
                "name": offer["source"],
                "region": offer.get("region", ""),
                "contact": offer.get("contact", {}),
                "products": [],
                "total": Decimal("0"),
                "currency": offer.get("currency", "EUR"),
            })
            by_supplier[key]["products"].append({
                "line": line,
                "price": offer.get("price", 0),
                "currency": offer.get("currency", "EUR"),
                "score": offer.get("score", 0),
            })
            try:
                by_supplier[key]["total"] += Decimal(str(offer.get("price", 0))) * line.quantity
            except Exception:
                pass

    # Grand total (meilleures offres)
    grand_total = sum((v["total"] for v in by_supplier.values()), Decimal("0"))

    return {
        "job": job,
        "company_name": settings.COMPANY_NAME,
        "company_email": settings.COMPANY_EMAIL,
        "reference": f"BATCH-{job.created_at:%Y%m%d}-{job.pk:05d}",
        "issued_at": timezone.now(),
        "user": job.user,
        "lines": lines,
        "resolved_lines": resolved,
        "unresolved_lines": [l for l in lines if not l.product_id],
        "ambiguous_lines": [l for l in lines if l.match_status == "ambiguous"],
        "by_supplier": list(by_supplier.values()),
        "grand_total": grand_total,
        "currency": "EUR",
        "stats": job.stats,
        "language_code": "fr",
    }