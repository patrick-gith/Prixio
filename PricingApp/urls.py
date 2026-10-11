# PricingApp/urls.py
from django.urls import path
from . import views

app_name = "PricingApp"

urlpatterns = [
    path("stats/", views.stats, name="stats"),
]