from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from audit.services import log_action

from .models import AdminCommand, Device


@receiver(post_save, sender=Device)
def device_post_save(sender, instance, created, update_fields=None, **kwargs):
    if created:
        log_action("device_created", f"Dodano urządzenie „{instance.name}”")
        return

    # zmiany automatyczne (monitoring, executor) nie zaśmiecają historii
    if update_fields:
        return

    log_action("device_updated", f"Zmieniono dane urządzenia „{instance.name}”")


@receiver(post_delete, sender=Device)
def device_post_delete(sender, instance, **kwargs):
    log_action("device_deleted", f"Usunięto urządzenie „{instance.name}”")


@receiver(post_save, sender=AdminCommand)
def admin_command_post_save(sender, instance, created, **kwargs):
    if created or instance.status not in (
        AdminCommand.CommandStatus.DONE,
        AdminCommand.CommandStatus.FAILED,
    ):
        return

    action = (
        "device_disconnected"
        if instance.command_type == AdminCommand.CommandType.DISCONNECT
        else "device_connected"
    )
    wynik = (
        "wykonano"
        if instance.status == AdminCommand.CommandStatus.DONE
        else "niepowodzenie"
    )
    log_action(
        action,
        f"Polecenie „{instance.get_command_type_display()}” dla urządzenia "
        f"{instance.device.name} - {wynik}",
    )
