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