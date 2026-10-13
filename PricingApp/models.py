from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Source(models.Model):
    name = models.CharField(_("Nom"), max_length=64)
    adapter_key = models.CharField(_("Clé adaptateur"), max_length=64)
    region = models.CharField(_("Région"), max_length=8)
    currency = models.CharField(_("Devise"), max_length=8)
    is_active = models.BooleanField(_("Active"), default=True)
    created_at = models.DateTimeField(_("Créée le"), auto_now_add=True)

    class Meta:
        verbose_name = _("Source")
        verbose_name_plural = _("Sources")
        unique_together = ("adapter_key", "region")

    def __str__(self):
        return f"{self.name} [{self.region}]"


class PricePoint(models.Model):
    product = models.ForeignKey(
        "CatalogApp.Product", on_delete=models.CASCADE,
        related_name="prices", verbose_name=_("Produit"),
    )
    source = models.ForeignKey(
        Source, on_delete=models.CASCADE, verbose_name=_("Source"),
    )
    price_local = models.DecimalField(
        _("Prix local"), max_digits=14, decimal_places=2,
    )
    currency = models.CharField(_("Devise"), max_length=8)
    price_base = models.DecimalField(
        _("Prix normalisé"), max_digits=14, decimal_places=2,
        null=True, blank=True,
    )
    in_stock = models.BooleanField(_("En stock"), default=True)
    captured_at = models.DateTimeField(_("Capturé le"), auto_now_add=True)

    class Meta:
        verbose_name = _("Relevé de prix")
        verbose_name_plural = _("Relevés de prix")
        ordering = ["-captured_at"]
        indexes = [
            models.Index(fields=["product", "captured_at"]),
            models.Index(fields=["product", "source"]),
        ]

    def __str__(self):
        return f"{self.product.title} · {self.source.name} = {self.price_local} {self.currency}"


class Watchlist(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="watchlists", verbose_name=_("Utilisateur"),
    )
    product = models.ForeignKey(
        "CatalogApp.Product", on_delete=models.CASCADE,
        verbose_name=_("Produit"),
    )
    target_score = models.PositiveSmallIntegerField(
        _("Score cible"), default=70,
    )
    created_at = models.DateTimeField(_("Créée le"), auto_now_add=True)

    class Meta:
        verbose_name = _("Veille")
        verbose_name_plural = _("Veilles")
        unique_together = ("user", "product")

    def __str__(self):
        return f"{self.user} → {self.product.title}"


class Alert(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="alerts", verbose_name=_("Utilisateur"),
    )
    product = models.ForeignKey(
        "CatalogApp.Product", on_delete=models.CASCADE,
        verbose_name=_("Produit"),
    )
    score = models.FloatField(_("Score"))
    message = models.TextField(_("Message"))
    is_read = models.BooleanField(_("Lue"), default=False)
    created_at = models.DateTimeField(_("Créée le"), auto_now_add=True)

    class Meta:
        verbose_name = _("Alerte")
        verbose_name_plural = _("Alertes")
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.score:.0f}] {self.product.title}"



class FxRate(models.Model):
    """Taux de change journalier, mis en cache pour éviter les appels API."""
    date = models.DateField(_("Date"), db_index=True)
    base = models.CharField(_("Devise de base"), max_length=8)
    quote = models.CharField(_("Devise cible"), max_length=8)
    rate = models.DecimalField(_("Taux"), max_digits=18, decimal_places=8)

    class Meta:
        unique_together = ("date", "base", "quote")
        indexes = [models.Index(fields=["date", "base", "quote"])]

    def __str__(self):
        return f"{self.date} 1 {self.base} = {self.rate} {self.quote}"


class CompetitorListing(models.Model):
    """Mode B — un vendeur surveillé pour un produit donné."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="listings",
    )
    product = models.ForeignKey(
        "CatalogApp.Product", on_delete=models.CASCADE,
        related_name="listings",
    )
    my_price = models.DecimalField(_("Mon prix"), max_digits=14, decimal_places=2)
    my_currency = models.CharField(_("Devise"), max_length=8)
    region = models.CharField(_("Région"), max_length=8, default="FR")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product", "region")
        ordering = ["-created_at"]


class PurchaseIntent(models.Model):
    """Mode C — intention d'achat avec deadline."""
    STATUS_CHOICES = [
        ("pending", _("En attente")),
        ("done", _("Conclu")),
        ("cancelled", _("Annulé")),
    ]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="intents",
    )
    product = models.ForeignKey(
        "CatalogApp.Product", on_delete=models.CASCADE,
        related_name="intents",
    )
    quantity = models.PositiveIntegerField(_("Quantité"), default=1)
    deadline = models.DateField(_("Date limite"))
    region = models.CharField(_("Région"), max_length=8, default="FR")
    status = models.CharField(
        _("Statut"), max_length=16, choices=STATUS_CHOICES, default="pending",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

# ==========================================================
# BATCH PROCUREMENT (Mode D)
# ==========================================================

class BatchJob(models.Model):
    """Une import de commande multi-lignes."""
    STATUS_CHOICES = [
        ("draft",       _("Brouillon")),
        ("verifying",   _("Vérification")),
        ("ready",       _("Prêt")),
        ("processing",  _("Analyse en cours")),
        ("done",        _("Terminé")),
        ("failed",      _("Échec")),
    ]

    PRIORITY_CHOICES = [
        ("price",     _("Prix le plus bas")),
        ("stock",     _("Disponibilité")),
        ("proximity", _("Proximité géographique")),
        ("rating",    _("Meilleure note vendeur")),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="batch_jobs", verbose_name=_("Utilisateur"),
    )

    # Fichier source
    original_file = models.FileField(
        _("Fichier source"), upload_to="batch/%Y/%m/",
    )
    original_name = models.CharField(_("Nom d'origine"), max_length=255)
    original_format = models.CharField(_("Format"), max_length=10)  # csv, xlsx, pdf, docx

    # Colonnes détectées + mapping utilisateur
    detected_columns = models.JSONField(_("Colonnes détectées"), default=list)
    column_mapping = models.JSONField(_("Mapping"), default=dict)

    # Critères de sélection
    criteria = models.JSONField(_("Critères"), default=dict)

    # Statut
    status = models.CharField(
        _("Statut"), max_length=16, choices=STATUS_CHOICES, default="draft",
    )
    progress = models.PositiveSmallIntegerField(_("Progression"), default=0)
    progress_message = models.CharField(_("Message"), max_length=255, blank=True, default="")

    # Résultat
    output_pdf = models.FileField(
        _("PDF généré"), upload_to="batch/output/%Y/%m/",
        null=True, blank=True,
    )
    stats = models.JSONField(_("Statistiques"), default=dict)
    error_message = models.TextField(_("Erreur"), blank=True, default="")

    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    completed_at = models.DateTimeField(_("Terminé le"), null=True, blank=True)

    class Meta:
        verbose_name = _("Import batch")
        verbose_name_plural = _("Imports batch")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Batch #{self.pk} — {self.original_name} ({self.get_status_display()})"

    @property
    def total_lines(self):
        return self.lines.count()

    @property
    def is_terminal(self):
        return self.status in ("done", "failed")


class BatchLine(models.Model):
    """Une ligne d'un import batch (un produit à sourcer)."""
    MATCH_STATUS = [
        ("pending",   _("En attente")),
        ("matched",   _("Correspondance trouvée")),
        ("ambiguous", _("Ambigu")),
        ("not_found", _("Introuvable")),
        ("manual",    _("Saisie manuelle")),
    ]

    job = models.ForeignKey(
        BatchJob, on_delete=models.CASCADE,
        related_name="lines", verbose_name=_("Import"),
    )
    row_number = models.PositiveIntegerField(_("N° ligne"))

    # Données brutes (toutes les colonnes d'origine)
    raw_data = models.JSONField(_("Données brutes"), default=dict)

    # Données extraites / normalisées
    designation = models.CharField(_("Désignation"), max_length=500)
    quantity = models.PositiveIntegerField(_("Quantité"), default=1)
    reference = models.CharField(_("Référence"), max_length=200, blank=True, default="")

    # Résolution
    product = models.ForeignKey(
        "CatalogApp.Product", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="batch_lines",
    )
    match_confidence = models.FloatField(_("Confiance"), default=0.0)
    match_status = models.CharField(
        _("Statut"), max_length=16, choices=MATCH_STATUS, default="pending",
    )

    # Résultats (offres trouvées)
    best_offers = models.JSONField(_("Meilleures offres"), default=list)
    chosen_offer = models.JSONField(_("Offre retenue"), default=dict)

    class Meta:
        verbose_name = _("Ligne batch")
        verbose_name_plural = _("Lignes batch")
        ordering = ["row_number"]
        unique_together = ("job", "row_number")

    def __str__(self):
        return f"#{self.row_number} {self.designation[:50]}"