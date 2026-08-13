from django.contrib.auth.signals import (
    user_logged_in,
    user_logged_out,
    user_login_failed,
)
from django.db.models.signals import post_save
from django.dispatch import receiver

from audit.services import log_action

from .models import User


@receiver(user_logged_in)
def on_login(sender, request, user, **kwargs):
    log_action("login", "Zalogowano do systemu", user=user, request=request)


@receiver(user_login_failed)
def on_login_failed(sender, credentials, request, **kwargs):
    username = (credentials or {}).get("username", "")
    log_action(
        "login_failed",
        "Nieudana próba logowania",
        username=username or "nieznany",
        request=request,
    )


@receiver(user_logged_out)
def on_logout(sender, request, user, **kwargs):
    if user is not None and getattr(user, "is_authenticated", False):
        log_action("logout", "Wylogowano z systemu", user=user, request=request)


@receiver(post_save, sender=User)
def on_user_created(sender, instance, created, **kwargs):
    if created:
        log_action(
            "user_created",
            f"Utworzono konto „{instance.username}” (rola: {instance.get_role_display()})",
        )
