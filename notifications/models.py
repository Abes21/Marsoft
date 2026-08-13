from django.db import models
from django.conf import settings


class Notification(models.Model):
    """Powiadomienie dla użytkownika o nowym alercie lub zdarzeniu."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="użytkownik",
    )
    alert = models.ForeignKey(
        "alerts.Alert",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
        verbose_name="alert",
    )
    message = models.CharField("wiadomość", max_length=255)
    is_read = models.BooleanField("przeczytane", default=False)
    created_at = models.DateTimeField("data utworzenia", auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Powiadomienie"
        verbose_name_plural = "Powiadomienia"

    def __str__(self):
        return f"{self.user.username}: {self.message}"
