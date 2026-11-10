from django.urls import path

from . import views

app_name = "SalesBotApp"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("services/", views.services_list, name="services_list"),
    path("services/new/", views.service_edit, name="service_new"),
    path("services/<int:pk>/edit/", views.service_edit, name="service_edit"),
    path("services/import/", views.import_csv, name="import_csv"),
    path("opportunities/", views.opportunities_list, name="opportunities_list"),
    path("opportunities/bulk/", views.opportunities_bulk, name="opportunities_bulk"),
    path("opportunities/<int:pk>/", views.opportunity_detail, name="opportunity_detail"),
    path("playground/", views.playground, name="playground"),
    path("channels/", views.channels, name="channels"),
    path("channels/<int:pk>/edit/", views.channel_edit, name="channel_edit"),
    path("search-queries/", views.search_queries, name="search_queries"),
    path("logs/", views.logs, name="logs"),
]
