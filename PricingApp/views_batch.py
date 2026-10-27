"""Vues du wizard batch : upload → verify → criteria → status → download."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _

from .models import BatchJob, BatchLine
from .parsers import SUPPORTED_EXTENSIONS, get_parser

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 Mo
MAX_LINES = 500


# ==========================================================
# ÉTAPE 1 — UPLOAD
# ==========================================================

@login_required
def batch_new(request):
    """Formulaire d'upload + parsing initial."""
    if request.method == "POST":
        file = request.FILES.get("file")
        if not file:
            messages.error(request, _("Aucun fichier fourni."))
            return redirect("PricingApp:batch_new")

        if file.size > MAX_FILE_SIZE:
            messages.error(request, _("Fichier trop volumineux (max 10 Mo)."))
            return redirect("PricingApp:batch_new")

        ext = file.name.rsplit(".", 1)[-1].lower()
        if ext not in SUPPORTED_EXTENSIONS:
            messages.error(
                request,
                _("Format non supporté. Utilisez : %(exts)s.")
                % {"exts": ", ".join(SUPPORTED_EXTENSIONS)},
            )
            return redirect("PricingApp:batch_new")

        # Créer le job
        job = BatchJob.objects.create(
            user=request.user,
            original_file=file,
            original_name=file.name,
            original_format=ext,
            status="verifying",
        )

        # Parser
        try:
            parser = get_parser(job.original_file.path)
            parsed = parser.parse(job.original_file.path)
        except Exception as exc:
            job.delete()
            messages.error(request, _("Impossible de lire le fichier : %(e)s.") % {"e": exc})
            return redirect("PricingApp:batch_new")

        if parsed.row_count == 0:
            job.delete()
            messages.error(request, _("Le fichier ne contient aucune ligne."))
            return redirect("PricingApp:batch_new")

        if parsed.row_count > MAX_LINES:
            job.delete()
            messages.error(
                request,
                _("Trop de lignes (%(n)s). Maximum : %(max)s.")
                % {"n": parsed.row_count, "max": MAX_LINES},
            )
            return redirect("PricingApp:batch_new")

        job.detected_columns = parsed.columns
        job.save(update_fields=["detected_columns"])

        # Créer les lignes en base
        for row in parsed.rows:
            BatchLine.objects.create(
                job=job,
                row_number=row.row_number,
                raw_data=row.raw,
                designation="",  # rempli à l'étape suivante
            )

        # Auto-guess du mapping de colonnes
        mapping = _guess_mapping(parsed.columns)
        job.column_mapping = mapping
        job.save(update_fields=["column_mapping"])

        return redirect("PricingApp:batch_verify", job_id=job.pk)

    return render(request, "PricingApp/batch/step1_upload.html", {
        "supported": SUPPORTED_EXTENSIONS,
        "max_size_mb": MAX_FILE_SIZE // (1024 * 1024),
        "max_lines": MAX_LINES,
    })


# ==========================================================
# ÉTAPE 2 — VÉRIFICATION / MAPPING
# ==========================================================

@login_required
def batch_verify(request, job_id: int):
    """Mapping des colonnes + aperçu + édition manuelle."""
    job = get_object_or_404(BatchJob, pk=job_id, user=request.user)

    if job.status not in ("verifying", "draft"):
        return redirect("PricingApp:batch_status", job_id=job.pk)

    if request.method == "POST":
        # Mapping
        mapping = {
            "designation": request.POST.get("col_designation", ""),
            "quantity":    request.POST.get("col_quantity", ""),
            "reference":   request.POST.get("col_reference", ""),
        }

        if not mapping["designation"]:
            messages.error(request, _("La colonne « Désignation » est obligatoire."))
            return redirect("PricingApp:batch_verify", job_id=job.pk)

        job.column_mapping = mapping

        # Overrides manuels par ligne
                # Overrides manuels par ligne
        # Format attendu : override_<line_id>_<field>
        # Ex : override_42_designation, override_42_quantity, override_42_reference
        overrides: dict[int, dict] = {}
        for key, value in request.POST.items():
            if not key.startswith("override_"):
                continue
            parts = key.split("_", 2)   # ['override', '<id>', '<field>']
            if len(parts) != 3:
                continue
            try:
                line_id = int(parts[1])
            except ValueError:
                continue
            field = parts[2]            # 'designation' | 'quantity' | 'reference'
            overrides.setdefault(line_id, {})[field] = value.strip()

                # Appliquer le mapping + overrides
        for line in job.lines.all():
            raw = line.raw_data
            line_override = overrides.get(line.pk, {})

            desig = line_override.get("designation") or raw.get(mapping["designation"], "")
            qty_raw = line_override.get("quantity") or raw.get(mapping["quantity"], "1")
            ref = line_override.get("reference") or raw.get(mapping["reference"], "")

            line.designation = str(desig).strip()[:500]
            line.reference = str(ref).strip()[:200]

            try:
                line.quantity = max(1, int(float(str(qty_raw).replace(",", "."))))
            except (ValueError, TypeError):
                line.quantity = 1

            line.save(update_fields=["designation", "quantity", "reference"])
        job.status = "ready"
        job.save(update_fields=["column_mapping", "status"])

        return redirect("PricingApp:batch_criteria", job_id=job.pk)

    # GET : afficher
    lines = list(job.lines.all()[:20])  # preview 20 premières
    total_lines = job.total_lines

    return render(request, "PricingApp/batch/step2_verify.html", {
        "job": job,
        "columns": job.detected_columns,
        "mapping": job.column_mapping,
        "preview_lines": lines,
        "total_lines": total_lines,
        "has_more": total_lines > 20,
    })


# ==========================================================
# ÉTAPE 3 — CRITÈRES
# ==========================================================

@login_required
def batch_criteria(request, job_id: int):
    """Choix des critères d'analyse."""
    job = get_object_or_404(BatchJob, pk=job_id, user=request.user)

    if job.status not in ("ready", "verifying"):
        return redirect("PricingApp:batch_status", job_id=job.pk)

    if request.method == "POST":
        criteria = {
            "priority":        request.POST.get("priority", "price"),
            "max_suppliers":   int(request.POST.get("max_suppliers", 3)),
            "region":          request.POST.get("region", "FR"),
            "include_used":    request.POST.get("include_used") == "on",
            "language":        request.POST.get("language", "fr"),
        }
        job.criteria = criteria
        job.status = "processing"
        job.progress = 0
        job.progress_message = _("En attente d'un worker…")
        job.save()

        # Envoie la tâche à Celery (retour en ~50 ms)
        from .tasks import process_batch_task
        process_batch_task.delay(job.pk)

        return redirect("PricingApp:batch_status", job_id=job.pk)

    return render(request, "PricingApp/batch/step3_criteria.html", {
        "job": job,
        "total_lines": job.total_lines,
    })


# ==========================================================
# ÉTAPE 4 — SUIVI (polling)
# ==========================================================

@login_required
def batch_status(request, job_id: int):
    """Affiche la progression ou redirige vers le téléchargement."""
    job = get_object_or_404(BatchJob, pk=job_id, user=request.user)

    if job.status == "done" and job.output_pdf:
        return redirect("PricingApp:batch_download", job_id=job.pk)

    return render(request, "PricingApp/batch/step4_status.html", {
        "job": job,
    })


@login_required
def batch_status_json(request, job_id: int):
    """Endpoint AJAX pour le polling."""
    job = get_object_or_404(BatchJob, pk=job_id, user=request.user)
    return JsonResponse({
        "status": job.status,
        "progress": job.progress,
        "message": job.progress_message,
        "redirect": (
            reverse("PricingApp:batch_download", args=[job.pk])
            if job.status == "done"
            else reverse("PricingApp:batch_status", args=[job.pk])
            if job.status == "failed"
            else None
        ),
    })


# ==========================================================
# ÉTAPE 5 — TÉLÉCHARGEMENT
# ==========================================================

@login_required
def batch_download(request, job_id: int):
    """Page de téléchargement ou envoi direct du PDF."""
    job = get_object_or_404(BatchJob, pk=job_id, user=request.user)

    if request.GET.get("raw") == "1":
        if not job.output_pdf:
            messages.error(request, _("PDF non disponible."))
            return redirect("PricingApp:batch_status", job_id=job.pk)
        response = FileResponse(
            job.output_pdf.open("rb"),
            content_type="application/pdf",
            as_attachment=True,
            filename=f"commande-{job.pk:05d}.pdf",
        )
        return response

    return render(request, "PricingApp/batch/step5_download.html", {
        "job": job,
        "stats": job.stats,
    })


# ==========================================================
# HELPERS
# ==========================================================

def _guess_mapping(columns: list[str]) -> dict:
    """Devine automatiquement les colonnes à partir des noms."""
    mapping = {"designation": "", "quantity": "", "reference": ""}
    if not columns:
        return mapping

    keywords = {
        "designation": ["désignation", "designation", "produit", "article",
                        "libellé", "libelle", "description", "name", "title"],
        "quantity":    ["quantité", "quantite", "qté", "qte", "qty", "quantite",
                        "nombre", "quantity"],
        "reference":   ["référence", "reference", "ref", "code", "sku", "isbn",
                        "ean", "gtin", "réf"],
    }
    cols_lower = {c: c.lower() for c in columns}
    for field, words in keywords.items():
        for col, lc in cols_lower.items():
            if any(w in lc for w in words):
                mapping[field] = col
                break
    return mapping