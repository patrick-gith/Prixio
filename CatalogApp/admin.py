from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("title", "primary_id", "canonical_type", "brand", "created_at")
    list_filter = ("canonical_type",)
    search_fields = ("title", "primary_id", "brand")

    class Meta:
        verbose_name = _("Produit")