from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CatalogAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "CatalogApp"
    verbose_name = _("Catalogue")