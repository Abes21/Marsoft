from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.shortcuts import render
from django.utils import timezone

from alerts.models import Alert
from devices.models import Device
from logs.models import LogEntry


@login_required
def dashboard(request):
    """Dashboard z aktualnym stanem infrastruktury (RF-08–RF-11)."""

    devices_qs = Device.objects.all()

    stats = {
        "devices_total": devices_qs.count(),
        "devices_online": devices_qs.filter(
            monitoring_status=Device.MonitoringStatus.ONLINE
        ).count(),
        "devices_offline": devices_qs.filter(
            monitoring_status=Device.MonitoringStatus.OFFLINE
        ).count(),
        "devices_unknown": devices_qs.filter(
            monitoring_status=Device.MonitoringStatus.UNKNOWN
        ).count(),
        "devices_disconnected": devices_qs.filter(
            network_access_status=Device.NetworkAccessStatus.DISCONNECTED_ADMIN
        ).count(),
    }

    unresolved = [Alert.Status.NEW, Alert.Status.IN_PROGRESS]
    alert_stats = {
        "alerts_new": Alert.objects.filter(status=Alert.Status.NEW).count(),
        "alerts_unresolved": Alert.objects.filter(status__in=unresolved).count(),
        "alerts_critical": Alert.objects.filter(
            severity=Alert.Severity.CRITICAL,
            status__in=unresolved,
        ).count(),
    }

    recent_logs = LogEntry.objects.select_related("device").order_by("-event_time")[:10]
    recent_alerts = Alert.objects.select_related("device").order_by("-created_at")[:10]

    # Wykres liczby zdarzeń z ostatnich 7 dni (RF-11)
    today = timezone.localdate()
    start_day = today - timedelta(days=6)

    counts = (
        LogEntry.objects.filter(event_time__date__gte=start_day)
        .annotate(day=TruncDate("event_time"))
        .values("day")
        .annotate(count=Count("id"))
        .order_by("day")
    )
    counts_by_day = {row["day"]: row["count"] for row in counts}

    chart_data = []
    for offset in range(7):
        day = start_day + timedelta(days=offset)
        chart_data.append(
            {
                "label": day.strftime("%d.%m"),
                "count": counts_by_day.get(day, 0),
            }
        )

    max_count = max([d["count"] for d in chart_data] + [1])

    context = {
        **stats,
        **alert_stats,
        "recent_logs": recent_logs,
        "recent_alerts": recent_alerts,
        "chart_data": chart_data,
        "max_count": max_count,
    }
    return render(request, "core/dashboard.html", context)


@login_required
def settings_view(request):
    return render(request, "core/settings.html")
