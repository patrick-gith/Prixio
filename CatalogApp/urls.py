# CatalogApp/urls.py
from django.urls import path
from . import views

app_name = "CatalogApp"

urlpatterns = [
    path("catalog/", views.product_list, name="product_list"),
]