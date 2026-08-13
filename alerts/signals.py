from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from audit.services import log_action

from .models import Alert


@receiver(pre_save, sender=Alert)
def alert_pre_save(sender, instance, **kwargs):
    if instance.pk:
        try:
            instance._old_status = Alert.objects.get(pk=instance.pk).status
        except Alert.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(post_save, sender=Alert)
def alert_post_save(sender, instance, created, **kwargs):
    if created:
        return

    old = getattr(instance, "_old_status", None)
    if old and old != instance.status:
        log_action(
            "alert_status_changed",
            f"Zmieniono status alertu „{instance.name}”: "
            f"{Alert.Status(old).label} → {Alert.Status(instance.status).label}",
        )
