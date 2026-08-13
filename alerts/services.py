from datetime import timedelta

from django.utils import timezone

from devices.models import Device
from logs.models import LogEntry

from .models import Alert, AlertHistory, SecurityRule
from notifications.models import Notification
from accounts.models import User


def analyze_log_entry(log_entry):
    """Analizuje pojedynczy log i tworzy alerty na podstawie aktywnych reguł."""

    rules = SecurityRule.objects.filter(is_active=True)

    for rule in rules:
        if rule.rule_type == SecurityRule.RuleType.FAILED_LOGIN:
            check_failed_login_rule(rule, log_entry)

        elif rule.rule_type == SecurityRule.RuleType.CRITICAL_EVENT:
            check_critical_event_rule(rule, log_entry)

        elif rule.rule_type == SecurityRule.RuleType.ADMIN_LOGIN:
            check_admin_login_rule(rule, log_entry)


def check_failed_login_rule(rule, log_entry):
    """Sprawdza regułę wielokrotnego nieudanego logowania."""

    if log_entry.event_type != "auth" or "failed" not in log_entry.message.lower():
        return

    time_threshold = timezone.now() - timedelta(minutes=rule.time_window_minutes)
    recent_failures = LogEntry.objects.filter(
        event_type="auth",
        message__icontains="failed",
        event_time__gte=time_threshold,
        device=log_entry.device,
    ).count()

    if recent_failures >= rule.threshold:
        create_alert_if_not_duplicate(
            rule=rule,
            name=f"Wielokrotne nieudane logowanie ({recent_failures} prób)",
            description=f"Wykryto {recent_failures} nieudanych prób logowania w ciągu {rule.time_window_minutes} minut.",
            device=log_entry.device,
            related_log=log_entry,
        )


def check_critical_event_rule(rule, log_entry):
    """Sprawdza regułę zdarzenia krytycznego."""

    if log_entry.level != LogEntry.LogLevel.CRITICAL:
        return

    create_alert_if_not_duplicate(
        rule=rule,
        name=f"Zdarzenie krytyczne: {log_entry.source}",
        description=log_entry.message,
        device=log_entry.device,
        related_log=log_entry,
    )


def check_admin_login_rule(rule, log_entry):
    """Sprawdza regułę logowania administratora."""

    if log_entry.event_type != "auth" or "admin" not in log_entry.user.lower():
        return

    create_alert_if_not_duplicate(
        rule=rule,
        name=f"Logowanie administratora: {log_entry.user}",
        description=f"Administrator {log_entry.user} zalogował się do systemu.",
        device=log_entry.device,
        related_log=log_entry,
    )


def check_device_unavailable(device):
    """Tworzy alert dla urządzenia krytycznego, które jest niedostępne."""

    if not device.is_critical or device.monitoring_status != Device.MonitoringStatus.OFFLINE:
        return

    rule = SecurityRule.objects.filter(
        rule_type=SecurityRule.RuleType.DEVICE_UNAVAILABLE,
        is_active=True,
    ).first()

    if not rule:
        return

    # Sprawdź, czy było kilka kolejnych nieudanych prób
    recent_results = device.monitoring_results.order_by("-checked_at")[:rule.threshold]
    if len(recent_results) < rule.threshold:
        return

    all_failed = all(not r.is_available for r in recent_results)
    if not all_failed:
        return

    create_alert_if_not_duplicate(
        rule=rule,
        name=f"Niedostępność urządzenia krytycznego: {device.name}",
        description=f"Urządzenie krytyczne {device.name} jest niedostępne od {rule.threshold} kolejnych sprawdzeń.",
        device=device,
    )


def create_alert_if_not_duplicate(rule, name, description, device=None, related_log=None):
    """Tworzy alert, jeśli nie istnieje już identyczny aktywny alert."""

    # Ochrona przed duplikatami (RF-59): nie twórz alertu, jeśli istnieje aktywny alert
    # dla tej samej reguły i urządzenia w ciągu ostatnich 5 minut
    time_threshold = timezone.now() - timedelta(minutes=5)
    existing_alert = Alert.objects.filter(
        rule=rule,
        device=device,
        status__in=[Alert.Status.NEW, Alert.Status.IN_PROGRESS],
        created_at__gte=time_threshold,
    ).exists()

    if existing_alert:
        return

    alert = Alert.objects.create(
        name=name,
        description=description,
        severity=rule.severity,
        rule=rule,
        device=device,
    )

    if related_log:
        alert.related_logs.add(related_log)

    # Zapisz historię utworzenia
    AlertHistory.objects.create(
        alert=alert,
        action_type=AlertHistory.ActionType.CREATED,
        description=f"Alert utworzony automatycznie przez regułę: {rule.name}",
    )

    # Utwórz powiadomienia dla administratorów (RF-71)
    create_notifications_for_alert(alert)
    return alert



def create_notifications_for_alert(alert):
    """Tworzy powiadomienia dla wszystkich administratorów o nowym alercie."""
    
    admins = User.objects.filter(role=User.Role.ADMIN)
    
    for admin in admins:
        Notification.objects.create(
            user=admin,
            alert=alert,
            message=f"Nowy alert {alert.get_severity_display()}: {alert.name}",
        )
