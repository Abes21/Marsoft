from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import admin_required

from .forms import DeviceForm
from .models import Device


@login_required
def device_list(request):
    """Lista urządzeń z wyszukiwaniem i filtrowaniem."""

    devices_qs = Device.objects.all().order_by("name")

    q = request.GET.get("q", "").strip()
    if q:
        devices_qs = devices_qs.filter(
            Q(name__icontains=q)
            | Q(ip_address__icontains=q)
            | Q(assigned_user__icontains=q)
            | Q(department__icontains=q)
        )

    filters = {
        "device_type": request.GET.get("device_type", ""),
        "monitoring_status": request.GET.get("monitoring_status", ""),
        "network_access_status": request.GET.get("network_access_status", ""),
        "operating_system": request.GET.get("operating_system", ""),
        "department": request.GET.get("department", ""),
        "importance": request.GET.get("importance", ""),
    }

    for field_name, value in filters.items():
        if value:
            devices_qs = devices_qs.filter(**{field_name: value})

    context = {
        "devices": devices_qs,
        "q": q,
        "filters": filters,
        "device_types": Device.DeviceType.choices,
        "monitoring_statuses": Device.MonitoringStatus.choices,
        "network_access_statuses": Device.NetworkAccessStatus.choices,
        "importances": Device.Importance.choices,
        "operating_systems": (
            Device.objects.exclude(operating_system="")
            .values_list("operating_system", flat=True)
            .distinct()
            .order_by("operating_system")
        ),
        "departments": (
            Device.objects.exclude(department="")
            .values_list("department", flat=True)
            .distinct()
            .order_by("department")
        ),
    }

    return render(request, "devices/list.html", context)


@login_required
def device_detail(request, pk):
    """Szczegóły urządzenia."""

    device = get_object_or_404(Device, pk=pk)
    return render(request, "devices/detail.html", {"device": device})


@admin_required
def device_create(request):
    """Dodawanie urządzenia — tylko administrator."""

    form = DeviceForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        device = form.save()
        messages.success(request, f"Urządzenie „{device.name}” zostało dodane.")
        return redirect(device.get_absolute_url())

    return render(
        request,
        "devices/form.html",
        {
            "form": form,
            "title": "Dodaj urządzenie",
        },
    )


@admin_required
def device_update(request, pk):
    """Edycja urządzenia — tylko administrator."""

    device = get_object_or_404(Device, pk=pk)
    form = DeviceForm(request.POST or None, instance=device)

    if request.method == "POST" and form.is_valid():
        device = form.save()
        messages.success(request, f"Urządzenie „{device.name}” zostało zaktualizowane.")
        return redirect(device.get_absolute_url())

    return render(
        request,
        "devices/form.html",
        {
            "form": form,
            "device": device,
            "title": "Edytuj urządzenie",
        },
    )


@admin_required
def device_delete(request, pk):
    """Usuwanie urządzenia z potwierdzeniem — tylko administrator."""

    device = get_object_or_404(Device, pk=pk)

    if request.method == "POST":
        name = device.name
        device.delete()
        messages.success(request, f"Urządzenie „{name}” zostało usunięte.")
        return redirect("devices")

    return render(request, "devices/confirm_delete.html", {"device": device})


from .forms import AdminCommandForm
from .models import AdminCommand
from .services import execute_admin_command


@admin_required
def device_disconnect(request, pk):
    """Odłączenie urządzenia od sieci - tylko administrator."""

    device = get_object_or_404(Device, pk=pk)

    if device.disconnect_blocked:
        messages.error(
            request,
            "To urządzenie jest komponentem kluczowym dla działania aplikacji "
            "i nie może zostać odłączone od sieci.",
        )
        return redirect(device.get_absolute_url())

    allowed_statuses = (
        Device.NetworkAccessStatus.CONNECTED,
        Device.NetworkAccessStatus.COMMAND_ERROR,
    )
    if device.network_access_status not in allowed_statuses:
        messages.error(
            request,
            "Urządzenie nie może zostać odłączone w obecnym statusie dostępu do sieci.",
        )
        return redirect(device.get_absolute_url())

    form = AdminCommandForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        command = AdminCommand.objects.create(
            device=device,
            command_type=AdminCommand.CommandType.DISCONNECT,
            administrator=request.user,
            justification=form.cleaned_data["justification"],
        )
        command = execute_admin_command(command)

        if command.status == AdminCommand.CommandStatus.FAILED:
            messages.error(
                request,
                f"Nie udało się odłączyć urządzenia. {command.error_message} "
                "Możesz ponowić operację.",
            )
        else:
            messages.success(
                request,
                f"Urządzenie „{device.name}” zostało odłączone od sieci.",
            )
        return redirect(device.get_absolute_url())

    return render(
        request,
        "devices/command_confirm.html",
        {
            "device": device,
            "form": form,
            "command_label": "Odłącz od sieci",
            "is_disconnect": True,
        },
    )


@admin_required
def device_connect(request, pk):
    """Przywrócenie dostępu do sieci - tylko administrator."""

    device = get_object_or_404(Device, pk=pk)

    allowed_statuses = (
        Device.NetworkAccessStatus.DISCONNECTED_ADMIN,
        Device.NetworkAccessStatus.COMMAND_ERROR,
    )
    if device.network_access_status not in allowed_statuses:
        messages.error(
            request,
            "Urządzenie nie może zostać przyłączone w obecnym statusie dostępu do sieci.",
        )
        return redirect(device.get_absolute_url())

    form = AdminCommandForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        command = AdminCommand.objects.create(
            device=device,
            command_type=AdminCommand.CommandType.CONNECT,
            administrator=request.user,
            justification=form.cleaned_data["justification"],
        )
        command = execute_admin_command(command)

        if command.status == AdminCommand.CommandStatus.FAILED:
            messages.error(
                request,
                f"Nie udało się przyłączyć urządzenia. {command.error_message} "
                "Możesz ponowić operację.",
            )
        else:
            messages.success(
                request,
                f"Urządzeniu „{device.name}” przywrócono dostęp do sieci.",
            )
        return redirect(device.get_absolute_url())

    return render(
        request,
        "devices/command_confirm.html",
        {
            "device": device,
            "form": form,
            "command_label": "Przyłącz do sieci",
            "is_disconnect": False,
        },
    )


import ipaddress
import logging
import subprocess

from django.conf import settings
from django.utils import timezone

from .models import NetworkScan
from .services import run_nmap_discovery

logger = logging.getLogger(__name__)


def validate_subnet(value):
    """Walidacja podsieci CIDR po stronie serwera (RNF-10)."""

    try:
        network = ipaddress.ip_network(value, strict=False)
    except ValueError:
        return None

    if network.version != 4:
        return None

    if network.num_addresses > 256:
        return None

    return network


@admin_required
def device_scan(request):
    """Wykrywanie urządzeń w sieci - tylko administrator."""

    error = None
    detected = []
    subnet_value = (
        request.POST.get("subnet", "").strip() if request.method == "POST" else ""
    )

    if request.method == "POST":
        network = validate_subnet(subnet_value)

        if network is None:
            error = (
                "Podaj poprawną podsieć w formacie CIDR, np. 192.168.1.0/24 "
                "(maksymalnie 256 adresów)."
            )
        else:
            scan = NetworkScan.objects.create(
                subnet=str(network),
                administrator=request.user,
            )

            try:
                timeout = getattr(settings, "NETWORK_SCAN_TIMEOUT_SECONDS", 60)
                hosts = run_nmap_discovery(str(network), timeout=timeout)
                scan.status = NetworkScan.ScanStatus.DONE
                scan.hosts_found = hosts
            except FileNotFoundError:
                logger.exception("Brak zainstalowanego nmap.")
                scan.status = NetworkScan.ScanStatus.FAILED
                scan.error_message = "Brak narzędzia nmap na serwerze."
                error = "Brak zainstalowanego narzędzia nmap."
            except subprocess.TimeoutExpired:
                logger.exception("Przekroczono czas skanowania.")
                scan.status = NetworkScan.ScanStatus.FAILED
                scan.error_message = "Przekroczono limit czasu skanowania."
                error = "Skanowanie przekroczyło limit czasu."
            except Exception:
                logger.exception("Błąd skanowania sieci.")
                scan.status = NetworkScan.ScanStatus.FAILED
                scan.error_message = "Nie udało się zakończyć skanowania."
                error = "Nie udało się zakończyć skanowania."

            scan.finished_at = timezone.now()
            scan.save()

            if scan.status == NetworkScan.ScanStatus.DONE:
                existing_ips = set(
                    Device.objects.exclude(ip_address=None).values_list(
                        "ip_address", flat=True
                    )
                )
                detected = [
                    {
                        "ip": host["ip"],
                        "hostname": host["hostname"],
                        "exists": host["ip"] in existing_ips,
                    }
                    for host in scan.hosts_found
                ]

                if not detected:
                    error = "Nie wykryto żadnych aktywnych hostów w podanej podsieci."

    context = {
        "error": error,
        "detected": detected,
        "subnet": subnet_value,
        "scans": NetworkScan.objects.all()[:10],
    }
    return render(request, "devices/scan.html", context)


@admin_required
def device_scan_add(request):
    """Dodanie zaznaczonych wykrytych hostów do rejestru."""

    if request.method != "POST":
        return redirect("device_scan")

    added = 0
    skipped = 0

    for ip in request.POST.getlist("add_ips"):
        try:
            ipaddress.ip_address(ip)
        except ValueError:
            continue

        if Device.objects.filter(ip_address=ip).exists():
            skipped += 1
            continue

        Device.objects.create(
            name=f"NET-{ip}",
            ip_address=ip,
            device_type=Device.DeviceType.OTHER,
            monitoring_status=Device.MonitoringStatus.UNKNOWN,
            notes="Urządzenie wykryte skanem sieci (nmap).",
        )
        added += 1

    messages.success(
        request,
        f"Dodano {added} urządzeń do rejestru. Pominięto {skipped} już istniejących.",
    )
    return redirect("device_scan")
