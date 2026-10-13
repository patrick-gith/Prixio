# PrixioApp/models.py — REMPLACER le contenu actuel
from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _


class UserProfile(models.Model):
    """Préférences par utilisateur — région + devise d'affichage."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="prixio_profile",
    )
    region = models.CharField(_("Région"), max_length=8, default="FR")
    currency = models.CharField(_("Devise"), max_length=8, default="EUR")
    telegram_chat_id = models.CharField(
        _("Telegram chat ID"), max_length=64, blank=True, default="",
    )
    alert_threshold = models.PositiveSmallIntegerField(
        _("Seuil d'alerte"), default=75,
    )
    email_alerts = models.BooleanField(_("Alertes par email"), default=True)

    def __str__(self):
        return f"Profil de {self.user.username} ({self.region}/{self.currency})"


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)