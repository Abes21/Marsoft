from django.contrib import admin

from .models import LogEntry


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    list_display = ["event_time", "level", "source", "device", "event_type"]
    list_filter = ["level", "source", "event_type"]
    search_fields = ["message", "user"]
