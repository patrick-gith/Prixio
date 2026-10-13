from django.urls import path
from . import views

app_name = "CoreApp"

urlpatterns = [
    path("", views.home, name="home"),
    path("p/<path:identifier>/", views.analyze, name="analyze"),
    path("manifest.webmanifest", views.manifest, name="manifest"),
    path("service-worker.js", views.service_worker, name="service_worker"),
]