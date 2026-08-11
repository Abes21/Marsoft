import random

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import AdminCommand, Device


def execute_admin_command(command):
    """Demonstracyjny mechanizm wykonawczy poleceń administracyjnych.

    Symuluje przekazanie polecenia do agenta / kontrolera sieciowego.
    Prawdopodobieństwo niepowodzenia steruje ustawienie COMMAND_FAILURE_RATE.
    """

    command.status = AdminCommand.CommandStatus.RUNNING
    command.save(update_fields=["status"])

    failure_rate = getattr(settings, "COMMAND_FAILURE_RATE", 0.0)
    failed = random.random() < failure_rate

    with transaction.atomic():
        command = AdminCommand.objects.select_for_update().get(pk=command.pk)
        device = Device.objects.select_for_update().get(pk=command.device_id)

        if failed:
            # RF-32: nieudane polecenie nie zmienia błędnie statusu urządzenia.
            command.status = AdminCommand.CommandStatus.FAILED
            command.error_message = (
                "Symulowane niepowodzenie: brak odpowiedzi mechanizmu wykonawczego."
            )
            device.network_access_status = Device.NetworkAccessStatus.COMMAND_ERROR
        else:
            command.status = AdminCommand.CommandStatus.DONE
            command.result_message = "Polecenie wykonane pomyślnie (tryb demonstracyjny)."

            if command.command_type == AdminCommand.CommandType.DISCONNECT:
                device.network_access_status = (
                    Device.NetworkAccessStatus.DISCONNECTED_ADMIN
                )
            else:
                device.network_access_status = Device.NetworkAccessStatus.CONNECTED

        command.finished_at = timezone.now()
        device.last_admin_command_at = timezone.now()
        command.save()
        device.save()

    return command


import subprocess
import xml.etree.ElementTree as ET


def run_nmap_discovery(subnet, timeout=60):
    """Wykrywa aktywne hosty w podsieci za pomocą nmap -sn."""

    result = subprocess.run(
        ["nmap", "-sn", subnet, "-oX", "-"],
        capture_output=True,
        text=True,
        timeout=timeout,
    )

    root = ET.fromstring(result.stdout)
    hosts = []

    for host in root.findall("host"):
        status = host.find("status")
        if status is None or status.get("state") != "up":
            continue

        address = None
        for addr in host.findall("address"):
            if addr.get("addrtype") == "ipv4":
                address = addr.get("addr")
                break

        if not address:
            continue

        hostname = ""
        hostnames = host.find("hostnames")
        if hostnames is not None:
            first = hostnames.find("hostname")
            if first is not None:
                hostname = first.get("name", "")

        hosts.append({"ip": address, "hostname": hostname})

    return hosts
