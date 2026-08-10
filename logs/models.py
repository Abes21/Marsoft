from django.db import models


class LogEntry(models.Model):
    """Pojedynczy wpis logu."""

    class LogLevel(models.TextChoices):
        DEBUG = "debug", "Debug"
        INFO = "info", "Informacja"
        WARNING = "warning", "Ostrzeżenie"
        ERROR = "error", "Błąd"
        CRITICAL = "critical", "Krytyczny"

    event_time = models.DateTimeField("czas zdarzenia", db_index=True)
    received_time = models.DateTimeField("czas odbioru", auto_now_add=True, db_index=True)
    source = models.CharField("źródło", max_length=100, db_index=True)
    device = models.ForeignKey(
        "devices.Device",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="logs",
        verbose_name="urządzenie",
    )
    user = models.CharField("użytkownik", max_length=100, blank=True, db_index=True)
    event_type = models.CharField("typ zdarzenia", max_length=100, db_index=True)
    level = models.CharField("poziom", max_length=20, choices=LogLevel.choices, db_index=True)
    message = models.TextField("treść komunikatu")
    raw_data = models.JSONField("dane dodatkowe (JSON)", default=dict, blank=True)

    class Meta:
        ordering = ["-event_time"]
        verbose_name = "Log"
        verbose_name_plural = "Logi"

    def __str__(self):
        return f"[{self.get_level_display()}] {self.source}: {self.message[:50]}"
