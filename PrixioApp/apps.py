from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PrixioAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "PrixioApp"
    verbose_name = _("Prixio")