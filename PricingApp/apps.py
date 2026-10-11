from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PricingAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "PricingApp"
    verbose_name = _("Tarification")