from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("devices/", include("devices.urls")),
    path("logs/", include("logs.urls")),
    path("api/", include("logs.api_urls")),
    path("alerts/", include("alerts.urls")),
    path("audit/", include("audit.urls")),
    path("notifications/", include("notifications.urls")),
    path("", include("core.urls")),
]
