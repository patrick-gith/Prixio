# PricingApp/urls.py
from django.urls import path
from . import views
from . import api
app_name = "PricingApp"

urlpatterns = [
    path("stats/", views.stats, name="stats"),
    path("competitor/", views.competitor_dashboard, name="competitor"),
    path("procurement/", views.procurement_dashboard, name="procurement"),
    path("stats/", views.stats, name="stats"),
    path(
        "procurement/<int:intent_id>/pdf/",
        views.purchase_order_pdf,
        name="purchase_order_pdf",
    ),
    path("api/v1/analyze/", api.api_analyze, name="api_analyze"),
    path("api/v1/product/<int:product_id>/", api.api_product, name="api_product"),
]