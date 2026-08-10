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
