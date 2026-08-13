from django.conf import settings
from django.db import models


class ActivityLog(models.Model):
    """Historia działań użytkowników - tylko do odczytu (RF-80, RF-82)."""

    class ActionType(models.TextChoices):
        LOGIN = "login", "Logowanie"
        LOGIN_FAILED = "login_failed", "Nieudane logowanie"
        LOGOUT = "logout", "Wylogowanie"
        USER_CREATED = "user_created", "Utworzenie użytkownika"
        DEVICE_CREATED = "device_created", "Dodanie urządzenia"
        DEVICE_UPDATED = "device_updated", "Edycja urządzenia"
        DEVICE_DELETED = "device_deleted", "Usunięcie urządzenia"
        DEVICE_DISCONNECTED = "device_disconnected", "Odłączenie urządzenia od sieci"
        DEVICE_CONNECTED = "device_connected", "Przyłączenie urządzenia do sieci"
        ALERT_STATUS_CHANGED = "alert_status_changed", "Zmiana statusu alertu"
        SETTINGS_CHANGED = "settings_changed", "Zmiana ustawień"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activity_logs",
        verbose_name="użytkownik",
    )
    username = models.CharField("nazwa użytkownika", max_length=150, blank=True)
    action_type = models.CharField(
        "rodzaj operacji", max_length=30, choices=ActionType.choices, db_index=True
    )
    description = models.TextField("opis")
    ip_address = models.GenericIPAddressField("adres IP użytkownika", null=True, blank=True)
    created_at = models.DateTimeField("data", auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Działanie użytkownika"
        verbose_name_plural = "Działania użytkowników"

    def __str__(self):
        return f"{self.get_action_type_display()} - {self.username}"
