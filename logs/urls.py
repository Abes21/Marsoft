from django.urls import path

from . import views

urlpatterns = [
    path("", views.log_list, name="logs"),
    path("<int:pk>/", views.log_detail, name="log_detail"),
]
