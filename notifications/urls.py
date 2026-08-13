from django.urls import path

from . import views

urlpatterns = [
    path("", views.notification_list, name="notifications"),
    path("<int:pk>/read/", views.mark_as_read, name="notification_read"),
    path("read-all/", views.mark_all_as_read, name="notifications_read_all"),
]
