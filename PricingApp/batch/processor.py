"""Traitement complet d'un BatchJob : parsing → matching → collecte → PDF."""
import logging
from pathlib import Path

from django.utils import timezone

from ..models import BatchJob, BatchLine
from ..parsers import get_parser
from ..services import collect_prices_for
from ..analysis import analyze_product
from .matcher import match_line
from .supplier_finder import find_supplier_for_offer
from .pdf_builder import build_batch_pdf

logger = logging.getLogger(__name__)


def process_batch(job: BatchJob) -> None:
    """
    Traite un BatchJob de bout en bout. Ne lève pas — met à jour
    job.status et job.error_message à la fin.
    """
    try:
        _set_progress(job, 0, "Analyse du fichier…")

        # Étape 1 : matching des lignes
        lines = list(job.lines.all())
        total = len(lines)

        if total == 0:
            raise ValueError("Aucune ligne à traiter.")

        for i, line in enumerate(lines, start=1):
            _set_progress(
                job,
                int(5 + (i / total) * 40),
                f"Identification {i}/{total} — {line.designation[:40]}",
            )
            _resolve_line(line)

        # Étape 2 : collecte des prix pour les produits résolus
        resolved = [l for l in lines if l.product_id]
        for i, line in enumerate(resolved, start=1):
            _set_progress(
                job,
                int(45 + (i / max(len(resolved), 1)) * 35),
                f"Recherche prix {i}/{len(resolved)} — {line.designation[:40]}",
            )
            _collect_offers(line)

        # Étape 3 : génération du PDF
        _set_progress(job, 85, "Génération du PDF…")
        pdf_bytes = build_batch_pdf(job)

        # Sauvegarde
        from django.core.files.base import ContentFile
        filename = f"commande-{job.pk:05d}.pdf"
        job.output_pdf.save(filename, ContentFile(pdf_bytes), save=False)

        job.stats = _compute_stats(lines)
        job.status = "done"
        job.progress = 100
        job.progress_message = "Terminé"
        job.completed_at = timezone.now()
        job.save()

    except Exception as exc:
        logger.exception("Batch #%s failed", job.pk)
        job.status = "failed"
        job.error_message = str(exc)[:1000]
        job.completed_at = timezone.now()
        job.save(update_fields=["status", "error_message", "completed_at"])


def _set_progress(job: BatchJob, pct: int, message: str) -> None:
    job.progress = max(0, min(100, pct))
    job.progress_message = message
    job.status = "processing"
    job.save(update_fields=["progress", "progress_message", "status"])


def _resolve_line(line: BatchLine) -> None:
    """Résout la ligne → produit canonique."""
    result = match_line(line.designation, line.reference)
    line.product = result.product
    line.match_confidence = result.confidence
    line.match_status = result.status

    if result.status == "ambiguous":
        line.best_offers = [
            {"candidate": c["title"], "primary_id": c["primary_id"],
             "type": c["type"], "score": c["score"]}
            for c in result.candidates
        ]
    line.save(update_fields=["product", "match_confidence", "match_status", "best_offers"])


def _collect_offers(line: BatchLine) -> None:
    """Collecte les prix pour un produit résolu."""
    if not line.product_id:
        return
    try:
        collect_prices_for(line.product)
        analysis = analyze_product(line.product)

        offers = []
        if analysis.get("has_data"):
            # Best offer principale
            best = analysis.get("best_offer") or {}
            if best:
                contact = find_supplier_for_offer(
                    source_name=best.get("source", ""),
                    region=best.get("region", ""),
                    product=line.product,
                )
                offers.append({
                    "source":  best.get("source", ""),
                    "region":  best.get("region", ""),
                    "price":   best.get("price"),
                    "currency": best.get("currency"),
                    "url":     best.get("url", ""),
                    "contact": contact,
                    "score":   analysis.get("score", 0),
                })

            # Historique pour contexte
            offers.append({
                "history": analysis.get("history", [])[:5],
                "median":  analysis.get("baseline", {}).get("median"),
                "label":   analysis.get("label"),
            })

        line.best_offers = offers
        line.save(update_fields=["best_offers"])
    except Exception as exc:
        logger.warning("Collecte échouée pour ligne #%s : %s", line.pk, exc)


def _compute_stats(lines) -> dict:
    total = len(lines)
    matched = sum(1 for l in lines if l.match_status == "matched")
    ambiguous = sum(1 for l in lines if l.match_status == "ambiguous")
    not_found = sum(1 for l in lines if l.match_status == "not_found")
    with_offers = sum(1 for l in lines if l.best_offers and l.product_id)

    return {
        "total": total,
        "matched": matched,
        "ambiguous": ambiguous,
        "not_found": not_found,
        "with_offers": with_offers,
    }