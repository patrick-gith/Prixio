"""Envoi d'alertes (email + Telegram) après analyse d'un produit."""
import logging
from decimal import Decimal

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse

from .models import Alert, Watchlist
from .analysis import analyze_product

logger = logging.getLogger(__name__)


def evaluate_and_notify(product, request=None) -> int:
    """
    Évalue le produit, et si le score dépasse le seuil de chaque watcher,
    crée une Alert + envoie un email. Retourne le nombre d'alertes créées.
    """
    analysis = analyze_product(product)
    if not analysis.get("has_data"):
        return 0

    created = 0
    for w in Watchlist.objects.filter(product=product).select_related("user"):
        profile = getattr(w.user, "prixio_profile", None)
        threshold = profile.alert_threshold if profile else settings.DEFAULT_ALERT_THRESHOLD

        if analysis["score"] < threshold:
            continue

        message = _build_message(product, analysis)

        alert = Alert.objects.create(
            user=w.user, product=product,
            score=analysis["score"], message=message,
        )

        if profile and profile.email_alerts and w.user.email:
            try:
                _send_email(w.user, alert, analysis, request)
            except Exception as exc:
                logger.warning("Email alert failed for %s: %s", w.user.email, exc)

        created += 1

    return created


def _build_message(product, analysis) -> str:
    return (
        f"🔥 {product.title} — score {analysis['score']}/100\n"
        f"Prix actuel : {analysis['current_price']:.2f} {analysis['currency']}\n"
        f"Médiane 90j : {analysis['baseline']['median']:.2f} {analysis['currency']}\n"
        f"Écart       : -{analysis['deviation_pct']}%"
    )


def _send_email(user, alert, analysis, request=None):
    subject = f"[Prixio] 🔥 {alert.product.title} — score {analysis['score']}/100"
    body = render_to_string("PrixioApp/emails/alert.txt", {
        "user": user, "alert": alert, "analysis": analysis,
    })
    send_mail(
        subject=subject,
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )