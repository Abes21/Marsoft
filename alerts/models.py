from django.db import models
from django.conf import settings


class SecurityRule(models.Model):
    """Reguła bezpieczeństwa do analizy logów."""

    class RuleType(models.TextChoices):
        FAILED_LOGIN = "failed_login", "Wielokrotne nieudane logowanie"
        CRITICAL_EVENT = "critical_event", "Zdarzenie krytyczne"
        ADMIN_LOGIN = "admin_login", "Logowanie administratora"
        DEVICE_UNAVAILABLE = "device_unavailable", "Niedostępność urządzenia krytycznego"
        OUTSIDE_HOURS = "outside_hours", "Logowanie poza godzinami pracy"
        SERVICE_STOPPED = "service_stopped", "Zatrzymanie ważnej usługi"
        REPEATED_ERRORS = "repeated_errors", "Powtarzające się błędy z urządzenia"

    class Severity(models.TextChoices):
        INFO = "info", "Informacyjny"
        LOW = "low", "Niski"
        MEDIUM = "medium", "Średni"
        HIGH = "high", "Wysoki"
        CRITICAL = "critical", "Krytyczny"

    name = models.CharField("nazwa", max_length=200)
    description = models.TextField("opis", blank=True)
    rule_type = models.CharField(
        "typ reguły",
        max_length=30,
        choices=RuleType.choices,
    )
    threshold = models.PositiveIntegerField("próg wystąpień", default=5)
    time_window_minutes = models.PositiveIntegerField(
        "przedział czasowy (minuty)",
        default=10,
    )
    severity = models.CharField(
        "poziom zagrożenia alertu",
        max_length=20,
        choices=Severity.choices,
        default=Severity.MEDIUM,
    )
    is_active = models.BooleanField("aktywna", default=True)
    created_at = models.DateTimeField("data utworzenia", auto_now_add=True)
    updated_at = models.DateTimeField("data aktualizacji", auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Reguła bezpieczeństwa"
        verbose_name_plural = "Reguły bezpieczeństwa"

    def __str__(self):
        return self.name


class Alert(models.Model):
    """Alert bezpieczeństwa utworzony po spełnieniu warunków reguły."""

    class Severity(models.TextChoices):
        INFO = "info", "Informacyjny"
        LOW = "low", "Niski"
        MEDIUM = "medium", "Średni"
        HIGH = "high", "Wysoki"
        CRITICAL = "critical", "Krytyczny"

    class Status(models.TextChoices):
        NEW = "new", "Nowy"
        IN_PROGRESS = "in_progress", "W analizie"
        RESOLVED = "resolved", "Rozwiązany"
        FALSE_POSITIVE = "false_positive", "Fałszywy alarm"
        IGNORED = "ignored", "Zignorowany"

    name = models.CharField("nazwa", max_length=255)
    description = models.TextField("opis", blank=True)
    severity = models.CharField(
        "poziom zagrożenia",
        max_length=20,
        choices=Severity.choices,
    )
    status = models.CharField(
        "status",
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
        db_index=True,
    )
    rule = models.ForeignKey(
        SecurityRule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="alerts",
        verbose_name="reguła",
    )
    device = models.ForeignKey(
        "devices.Device",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="alerts",
        verbose_name="urządzenie",
    )
    related_logs = models.ManyToManyField(
        "logs.LogEntry",
        blank=True,
        related_name="alerts",
        verbose_name="powiązane logi",
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_alerts",
        verbose_name="osoba odpowiedzialna",
    )
    created_at = models.DateTimeField("data utworzenia", auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField("data aktualizacji", auto_now=True)
    resolved_at = models.DateTimeField("data rozwiązania", null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Alert"
        verbose_name_plural = "Alerty"

    def __str__(self):
        return f"{self.name} ({self.get_severity_display()})"


class AlertNote(models.Model):
    """Notatka do alertu dodana przez użytkownika."""

    alert = models.ForeignKey(
        Alert,
        on_delete=models.CASCADE,
        related_name="notes",
        verbose_name="alert",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="alert_notes",
        verbose_name="autor",
    )
    content = models.TextField("treść notatki")
    created_at = models.DateTimeField("data dodania", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Notatka do alertu"
        verbose_name_plural = "Notatki do alertów"

    def __str__(self):
        return f"Notatka do alertu #{self.alert_id} - {self.author}"


class AlertHistory(models.Model):
    """Historia zmian alertu: statusy, notatki, przypisania."""

    class ActionType(models.TextChoices):
        CREATED = "created", "Utworzono"
        STATUS_CHANGED = "status_changed", "Zmiana statusu"
        NOTE_ADDED = "note_added", "Dodano notatkę"
        ASSIGNED = "assigned", "Przypisano osobę"
        RESOLVED = "resolved", "Rozwiązano"

    alert = models.ForeignKey(
        Alert,
        on_delete=models.CASCADE,
        related_name="history",
        verbose_name="alert",
    )
    action_type = models.CharField(
        "rodzaj akcji",
        max_length=20,
        choices=ActionType.choices,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="alert_history_actions",
        verbose_name="użytkownik",
    )
    description = models.TextField("opis zmiany")
    created_at = models.DateTimeField("data akcji", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Historia alertu"
        verbose_name_plural = "Historie alertów"

    def __str__(self):
        return f"{self.get_action_type_display()} - Alert #{self.alert_id}"
