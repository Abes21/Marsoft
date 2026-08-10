from django.urls import path
from django.views.generic import RedirectView

from . import views

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="dashboard"), name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("logs/", views.logs_list, name="logs"),
    path("alerts/", views.alerts, name="alerts"),
    path("rules/", views.rules, name="rules"),
    path("settings/", views.settings_view, name="settings"),
]
