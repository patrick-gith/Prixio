# PricingApp/tasks.py
"""Tâches Celery pour le traitement asynchrone.

Chaque tâche est :
  - Idempotente (rejouable sans effet de bord)
  - Résiliente aux erreurs (retry automatique avec backoff)
  - Loguée (début, fin, erreurs)
"""
import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


# ==========================================================
# BATCH PROCUREMENT
# ==========================================================

@shared_task(
    name="pricing.process_batch",
    bind=True,
    queue="batch",
    max_retries=2,
    default_retry_delay=60,
)
def process_batch_task(self, job_id: int):
    """
    Traite un BatchJob en arrière-plan.

    Retourne un dict (utile pour Flower et les résultats Celery).
    """
    from .models import BatchJob
    from .batch import process_batch

    try:
        job = BatchJob.objects.get(pk=job_id)
    except BatchJob.DoesNotExist:
        logger.warning("BatchJob #%s introuvable, tâche annulée.", job_id)
        return {"ok": False, "error": "not_found", "job_id": job_id}

    # Idempotence : ne pas retraiter un job terminé
    if job.status in ("done", "failed"):
        logger.info("BatchJob #%s déjà en statut %s, skip.", job_id, job.status)
        return {"ok": True, "skipped": True, "job_id": job_id}

    logger.info("▶ Début traitement batch #%s (essai %s/%s)",
                job_id, self.request.retries + 1, self.max_retries + 1)

    try:
        process_batch(job)
        logger.info("✓ Fin traitement batch #%s (status=%s)", job_id, job.status)
        return {"ok": True, "status": job.status, "job_id": job_id}

    except Exception as exc:
        logger.exception("✗ Erreur traitement batch #%s", job_id)

        # Marque le job en échec si on a épuisé les retries
        if self.request.retries >= self.max_retries:
            job.status = "failed"
            job.error_message = str(exc)[:1000]
            job.completed_at = timezone.now()
            job.save(update_fields=["status", "error_message", "completed_at"])
            return {"ok": False, "error": str(exc), "job_id": job_id}

        # Sinon retry avec backoff
        raise self.retry(exc=exc)


# ==========================================================
# COLLECTE QUOTIDIENNE
# ==========================================================

@shared_task(
    name="pricing.collect_all_prices",
    bind=True,
    queue="collect",
    max_retries=1,
)
def collect_all_prices_task(self, product_id: int | None = None):
    """Collecte les prix (remplace le Cron Job Render)."""
    from django.core.management import call_command

    logger.info("▶ Démarrage collecte globale (product_id=%s)", product_id)
    try:
        kwargs = {}
        if product_id:
            kwargs["product_id"] = product_id
        call_command("collect_all", **kwargs)
        logger.info("✓ Collecte terminée")
        return {"ok": True}
    except Exception as exc:
        logger.exception("✗ Collecte échouée")
        raise self.retry(exc=exc)


# ==========================================================
# ÉVALUATION DES ALERTES
# ==========================================================

@shared_task(
    name="pricing.evaluate_alerts",
    bind=True,
    queue="collect",
)
def evaluate_alerts_task(self, product_id: int):
    """Évalue un produit et envoie les alertes si seuil dépassé."""
    from CatalogApp.models import Product
    from .alerts_service import evaluate_and_notify

    try:
        product = Product.objects.get(pk=product_id)
    except Product.DoesNotExist:
        return {"ok": False, "error": "not_found"}

    try:
        count = evaluate_and_notify(product)
        return {"ok": True, "alerts_created": count}
    except Exception as exc:
        logger.exception("Erreur évaluation alertes pour produit #%s", product_id)
        raise self.retry(exc=exc)