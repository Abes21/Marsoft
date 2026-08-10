from django.urls import path

from . import views

urlpatterns = [
    path("", views.alert_list, name="alerts"),
    path("<int:pk>/", views.alert_detail, name="alert_detail"),
    path("rules/", views.rule_list, name="rules"),
]
