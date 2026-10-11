from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Source, PricePoint, Watchlist, Alert


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ("name", "adapter_key", "region", "currency", "is_active")
    list_filter = ("region", "is_active")


@admin.register(PricePoint)
class PricePointAdmin(admin.ModelAdmin):
    list_display = ("product", "source", "price_local", "currency", "captured_at")
    list_filter = ("currency", "source")
    search_fields = ("product__title",)


@admin.register(Watchlist)
class WatchlistAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "target_score", "created_at")
    list_filter = ("target_score",)


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "score", "is_read", "created_at")
    list_filter = ("is_read",)