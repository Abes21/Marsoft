from django.urls import path

from . import views

urlpatterns = [
    path("", views.device_list, name="devices"),
    path("add/", views.device_create, name="device_add"),
    path("<int:pk>/", views.device_detail, name="device_detail"),
    path("<int:pk>/edit/", views.device_update, name="device_edit"),
    path("<int:pk>/delete/", views.device_delete, name="device_delete"),
    path("<int:pk>/disconnect/", views.device_disconnect, name="device_disconnect"),
    path("<int:pk>/connect/", views.device_connect, name="device_connect"),
]
