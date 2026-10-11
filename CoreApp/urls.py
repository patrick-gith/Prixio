from django.urls import path
from . import views

app_name = "CoreApp"

urlpatterns = [
    path("", views.home, name="home"),
    path("p/<path:identifier>/", views.analyze, name="analyze"),
]
