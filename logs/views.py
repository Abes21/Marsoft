import json
import logging
from datetime import datetime

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from alerts.services import analyze_log_entry
from devices.models import Device

from .models import LogEntry

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def ingest_logs(request):
    """Endpoint API do przyjmowania logów z zewnątrz (RF-43, RNF-15)."""

    api_key = request.headers.get("X-API-Key")
    expected_key = getattr(settings, "API_LOGS_KEY", "")

    if not expected_key or api_key != expected_key:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    if isinstance(payload, dict):
        payload = [payload]

    created_count = 0
    for log_data in payload:
        try:
            device = None
            device_ip = log_data.get("device_ip")
            if device_ip:
                device = Device.objects.filter(ip_address=device_ip).first()

            event_time_str = log_data.get("event_time")
            event_time = parse_datetime(event_time_str) if event_time_str else timezone.now()
            if event_time is None:
                event_time = timezone.now()
            if timezone.is_naive(event_time):
                event_time = timezone.make_aware(event_time)

            level = str(log_data.get("level", "info")).lower()
            if level not in dict(LogEntry.LogLevel.choices):
                level = LogEntry.LogLevel.INFO

            extra = log_data.get("extra", {})
            if not isinstance(extra, dict):
                extra = {}

            log = LogEntry.objects.create(
                event_time=event_time,
                source=str(log_data.get("source", "unknown"))[:100],
                device=device,
                user=str(log_data.get("user", ""))[:100],
                event_type=str(log_data.get("event_type", "generic"))[:100],
                level=level,
                message=str(log_data.get("message", "")),
                raw_data=extra,
            )

            # Analiza reguł bezpieczeństwa; błędny log nie może przerwać
            # przetwarzania pozostałych (RNF-25).
            try:
                analyze_log_entry(log)
            except Exception:
                logger.exception("Błąd analizy logu id=%s", log.pk)

            created_count += 1
        except Exception:
            logger.exception("Błąd zapisu logu")

    return JsonResponse({"status": "ok", "created": created_count}, status=201)


def parse_date(value, end_of_day=False):
    if not value:
        return None
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return None
    if end_of_day:
        parsed = parsed.replace(hour=23, minute=59, second=59)
    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed)
    return parsed


@login_required
def log_list(request):
    """Lista logów: wyszukiwanie, filtry i paginacja po stronie serwera."""

    qs = LogEntry.objects.select_related("device").all()

    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(
            Q(message__icontains=q)
            | Q(user__icontains=q)
            | Q(device__name__icontains=q)
            | Q(device__ip_address__icontains=q)
        )

    filters = {
        "level": request.GET.get("level", ""),
        "source": request.GET.get("source", ""),
        "event_type": request.GET.get("event_type", ""),
        "device": request.GET.get("device", ""),
        "user": request.GET.get("user", ""),
        "date_from": request.GET.get("date_from", ""),
        "date_to": request.GET.get("date_to", ""),
    }

    if filters["level"]:
        qs = qs.filter(level=filters["level"])
    if filters["source"]:
        qs = qs.filter(source=filters["source"])
    if filters["event_type"]:
        qs = qs.filter(event_type=filters["event_type"])
    if filters["device"]:
        qs = qs.filter(device_id=filters["device"])
    if filters["user"]:
        qs = qs.filter(user__icontains=filters["user"])

    date_from = parse_date(filters["date_from"])
    if date_from:
        qs = qs.filter(event_time__gte=date_from)
    date_to = parse_date(filters["date_to"], end_of_day=True)
    if date_to:
        qs = qs.filter(event_time__lte=date_to)

    paginator = Paginator(qs, 50)
    page_obj = paginator.get_page(request.GET.get("page"))

    querystring = request.GET.copy()
    querystring.pop("page", None)

    context = {
        "page_obj": page_obj,
        "q": q,
        "filters": filters,
        "base_qs": querystring.urlencode(),
        "levels": LogEntry.LogLevel.choices,
        "sources": LogEntry.objects.exclude(source="")
        .values_list("source", flat=True).distinct().order_by("source"),
        "event_types": LogEntry.objects.exclude(event_type="")
        .values_list("event_type", flat=True).distinct().order_by("event_type"),
        "devices": Device.objects.order_by("name"),
    }
    return render(request, "logs/list.html", context)


@login_required
def log_detail(request, pk):
    """Szczegóły pojedynczego logu."""

    log = get_object_or_404(LogEntry.objects.select_related("device"), pk=pk)
    context = {
        "log": log,
        "raw_pretty": json.dumps(log.raw_data, ensure_ascii=False, indent=2),
    }
    return render(request, "logs/detail.html", context)
