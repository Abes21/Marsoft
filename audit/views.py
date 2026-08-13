from datetime import datetime

from django.core.paginator import Paginator
from django.shortcuts import render
from django.utils import timezone

from accounts.decorators import admin_required

from .models import ActivityLog


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


@admin_required
def activity_list(request):
    """Historia działań - widok tylko do odczytu (RF-81, RF-82)."""

    qs = ActivityLog.objects.select_related("user").all()

    filters = {
        "action_type": request.GET.get("action_type", ""),
        "username": request.GET.get("username", ""),
        "date_from": request.GET.get("date_from", ""),
        "date_to": request.GET.get("date_to", ""),
    }

    if filters["action_type"]:
        qs = qs.filter(action_type=filters["action_type"])
    if filters["username"]:
        qs = qs.filter(username__icontains=filters["username"])

    date_from = parse_date(filters["date_from"])
    if date_from:
        qs = qs.filter(created_at__gte=date_from)
    date_to = parse_date(filters["date_to"], end_of_day=True)
    if date_to:
        qs = qs.filter(created_at__lte=date_to)

    paginator = Paginator(qs, 50)
    page_obj = paginator.get_page(request.GET.get("page"))

    querystring = request.GET.copy()
    querystring.pop("page", None)

    context = {
        "page_obj": page_obj,
        "filters": filters,
        "base_qs": querystring.urlencode(),
        "action_types": ActivityLog.ActionType.choices,
    }
    return render(request, "audit/list.html", context)
