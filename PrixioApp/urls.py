from django.urls import path
from . import views

app_name = "PrixioApp"

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
    path("watchlist/", views.watchlist, name="watchlist"),
    path("watchlist/add/<int:product_id>/", views.add_to_watchlist, name="add_to_watchlist"),
    path("watchlist/remove/<int:product_id>/", views.remove_from_watchlist, name="remove_from_watchlist"),
    path("alerts/", views.alerts, name="alerts"),
    path("refresh/", views.refresh_all, name="refresh_all"),
]
