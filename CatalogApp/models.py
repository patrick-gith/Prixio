from django.db import models
from django.utils.translation import gettext_lazy as _


class Product(models.Model):
    TYPE_BOOK = "book"
    TYPE_CRYPTO = "crypto"
    TYPE_ELECTRONICS = "electronics"
    TYPE_GAME = "game"
    TYPE_OTHER = "other"

    TYPE_CHOICES = [
        (TYPE_BOOK, _("Livre")),
        (TYPE_CRYPTO, _("Cryptomonnaie")),
        (TYPE_ELECTRONICS, _("Électronique")),
        (TYPE_GAME, _("Jeu vidéo")),
        (TYPE_OTHER, _("Autre")),
    ]

    canonical_type = models.CharField(
        _("Type"), max_length=32, choices=TYPE_CHOICES, default=TYPE_OTHER,
    )
    primary_id = models.CharField(
        _("Identifiant"), max_length=128, unique=True,
    )
    title = models.CharField(_("Titre"), max_length=255)
    brand = models.CharField(_("Marque"), max_length=128, blank=True)
    image_url = models.URLField(_("Image"), blank=True)
    attributes = models.JSONField(_("Attributs"), default=dict, blank=True)
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis à jour le"), auto_now=True)

    class Meta:
        verbose_name = _("Produit")
        verbose_name_plural = _("Produits")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.primary_id})"