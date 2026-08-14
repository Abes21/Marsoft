from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from devices.models import Device

from .forms import AlertNoteForm, AlertStatusForm, AlertFilterForm
from .models import Alert, AlertHistory, AlertNote, SecurityRule


@login_required
def alert_list(request):
    """Lista alertów z filtrami."""

    qs = Alert.objects.select_related("rule", "device", "assigned_to").all()

    form = AlertFilterForm(request.GET or None)
    if form.is_valid():
        if form.cleaned_data.get("status"):
            qs = qs.filter(status=form.cleaned_data["status"])
        if form.cleaned_data.get("severity"):
            qs = qs.filter(severity=form.cleaned_data["severity"])
        if form.cleaned_data.get("device"):
            qs = qs.filter(device=form.cleaned_data["device"])
        if form.cleaned_data.get("rule"):
            qs = qs.filter(rule=form.cleaned_data["rule"])
        if form.cleaned_data.get("assigned_to"):
            qs = qs.filter(assigned_to=form.cleaned_data["assigned_to"])
        if form.cleaned_data.get("date_from"):
            qs = qs.filter(created_at__gte=form.cleaned_data["date_from"])
        if form.cleaned_data.get("date_to"):
            qs = qs.filter(created_at__lte=form.cleaned_data["date_to"])

    paginator = Paginator(qs, 50)
    page_obj = paginator.get_page(request.GET.get("page"))

    querystring = request.GET.copy()
    querystring.pop("page", None)

    context = {
        "alerts": page_obj,
        "page_obj": page_obj,
        "base_qs": querystring.urlencode(),
        "filter_form": form,
        "devices": Device.objects.order_by("name"),
        "rules": SecurityRule.objects.order_by("name"),
    }
    return render(request, "alerts/list.html", context)


@login_required
def alert_detail(request, pk):
    """Szczegóły alertu z historią i notatkami."""

    alert = get_object_or_404(
        Alert.objects.select_related("rule", "device", "assigned_to"),
        pk=pk,
    )
    notes = alert.notes.select_related("author").all()
    history = alert.history.select_related("user").all()

    note_form = AlertNoteForm()
    status_form = AlertStatusForm(instance=alert)

    if request.method == "POST":
        if "add_note" in request.POST:
            note_form = AlertNoteForm(request.POST)
            if note_form.is_valid():
                note = note_form.save(commit=False)
                note.alert = alert
                note.author = request.user
                note.save()

                # Zapisz historię
                AlertHistory.objects.create(
                    alert=alert,
                    action_type=AlertHistory.ActionType.NOTE_ADDED,
                    user=request.user,
                    description=f"Dodano notatkę: {note.content[:50]}...",
                )

                messages.success(request, "Notatka została dodana.")
                return redirect("alert_detail", pk=alert.pk)

        elif "change_status" in request.POST:
            old_status = alert.status
            status_form = AlertStatusForm(request.POST, instance=alert)
            if status_form.is_valid():
                alert = status_form.save()

                if alert.status == Alert.Status.RESOLVED:
                    alert.resolved_at = timezone.now()
                    alert.save()

                # Zapisz historię
                AlertHistory.objects.create(
                    alert=alert,
                    action_type=AlertHistory.ActionType.STATUS_CHANGED,
                    user=request.user,
                    description=f"Zmieniono status z '{old_status}' na '{alert.status}'",
                )

                messages.success(request, "Status alertu został zmieniony.")
                return redirect("alert_detail", pk=alert.pk)

    context = {
        "alert": alert,
        "notes": notes,
        "history": history,
        "note_form": note_form,
        "status_form": status_form,
    }
    return render(request, "alerts/detail.html", context)


@login_required
def rule_list(request):
    """Lista reguł bezpieczeństwa - tylko administrator."""

    if not request.user.is_admin_role():
        messages.error(request, "Brak uprawnień.")
        return redirect("dashboard")

    rules = SecurityRule.objects.all()
    context = {"rules": rules}
    return render(request, "alerts/rules.html", context)
