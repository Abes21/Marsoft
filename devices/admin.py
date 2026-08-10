from django.contrib import admin

from .models import Device


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "device_type",
        "ip_address",
        "department",
        "importance",
        "monitoring_status",
        "network_access_status",
        "last_checked_at",
    ]
    list_filter = [
        "device_type",
        "importance",
        "monitoring_status",
        "network_access_status",
        "department",
    ]
    search_fields = [
        "name",
        "ip_address",
        "assigned_user",
        "department",
        "operating_system",
    ]


from .models import AdminCommand, MonitoringResult


@admin.register(AdminCommand)
class AdminCommandAdmin(admin.ModelAdmin):
    list_display = [
        "device",
        "command_type",
        "administrator",
        "status",
        "requested_at",
        "finished_at",
    ]
    list_filter = ["command_type", "status"]


@admin.register(MonitoringResult)
class MonitoringResultAdmin(admin.ModelAdmin):
    list_display = ["device", "checked_at", "is_available", "response_time_ms"]
    list_filter = ["is_available"]
