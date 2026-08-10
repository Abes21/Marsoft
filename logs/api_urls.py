from django.urls import path

from . import views

urlpatterns = [
    path("logs/ingest/", views.ingest_logs, name="api_ingest_logs"),
]
