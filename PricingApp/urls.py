# PricingApp/urls.py
from django.urls import path

from . import api, views, views_batch

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
    path("procurement/<int:intent_id>/pdf/", views.purchase_order_pdf, name="purchase_order_pdf"),

    # Batch (Mode D)
    path("batch/new/", views_batch.batch_new, name="batch_new"),
    path("batch/<int:job_id>/verify/", views_batch.batch_verify, name="batch_verify"),
    path("batch/<int:job_id>/criteria/", views_batch.batch_criteria, name="batch_criteria"),
    path("batch/<int:job_id>/status/", views_batch.batch_status, name="batch_status"),
    path("batch/<int:job_id>/status.json", views_batch.batch_status_json, name="batch_status_json"),
    path("batch/<int:job_id>/download/", views_batch.batch_download, name="batch_download"),
]