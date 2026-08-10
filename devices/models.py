from django.conf import settings
from django.db import models
from django.urls import reverse


class Device(models.Model):
    """Urządzenie firmowej infrastruktury IT."""

    class DeviceType(models.TextChoices):
        COMPUTER = "computer", "Komputer"
        LAPTOP = "laptop", "Laptop"
        SERVER = "server", "Serwer"
        PRINTER = "printer", "Drukarka"
        ROUTER = "router", "Router"
        SWITCH = "switch", "Switch"
        MOBILE = "mobile", "Urządzenie mobilne"
        OTHER = "other", "Inne"

    class MonitoringStatus(models.TextChoices):
        ONLINE = "online", "Online"
        OFFLINE = "offline", "Offline"
        UNKNOWN = "unknown", "Nieznany"
        DISABLED = "disabled", "Wyłączone z monitoringu"

    class NetworkAccessStatus(models.TextChoices):
        CONNECTED = "connected", "Przyłączone"
        DISCONNECTED_ADMIN = "disconnected_admin", "Odłączone administracyjnie"
        PENDING_DISCONNECT = "pending_disconnect", "Oczekuje na odłączenie"
        PENDING_CONNECT = "pending_connect", "Oczekuje na przyłączenie"
        COMMAND_ERROR = "command_error", "Błąd wykonania polecenia"

    class Importance(models.TextChoices):
        LOW = "low", "Niski"
        STANDARD = "standard", "Standardowy"
        HIGH = "high", "Wysoki"
        CRITICAL = "critical", "Krytyczny"

    name = models.CharField("nazwa", max_length=200)
    device_type = models.CharField(
        "typ urządzenia",
        max_length=20,
        choices=DeviceType.choices,
        default=DeviceType.COMPUTER,
    )
    ip_address = models.GenericIPAddressField(
        "adres IP",
        blank=True,
        null=True,
    )
    mac_address = models.CharField("adres MAC", max_length=17, blank=True)
    operating_system = models.CharField("system operacyjny", max_length=120, blank=True)
    assigned_user = models.CharField("użytkownik / właściciel", max_length=120, blank=True)
    department = models.CharField("dział", max_length=120, blank=True)
    location = models.CharField("lokalizacja", max_length=160, blank=True)

    importance = models.CharField(
        "poziom ważności",
        max_length=20,
        choices=Importance.choices,
        default=Importance.STANDARD,
    )

    monitoring_status = models.CharField(
        "status monitoringu",
        max_length=20,
        choices=MonitoringStatus.choices,
        default=MonitoringStatus.UNKNOWN,
    )

    network_access_status = models.CharField(
        "status dostępu do sieci",
        max_length=30,
        choices=NetworkAccessStatus.choices,
        default=NetworkAccessStatus.CONNECTED,
    )

    monitoring_enabled = models.BooleanField("monitoring włączony", default=True)

    disconnect_blocked = models.BooleanField(
        "ochrona przed odłączeniem (komponent kluczowy dla aplikacji)",
        default=False,
    )

    last_checked_at = models.DateTimeField(
        "data ostatniego sprawdzenia",
        blank=True,
        null=True,
    )
    last_admin_command_at = models.DateTimeField(
        "data ostatniego polecenia administracyjnego",
        blank=True,
        null=True,
    )

    notes = models.TextField("uwagi", blank=True)

    created_at = models.DateTimeField("data utworzenia", auto_now_add=True)
    updated_at = models.DateTimeField("data aktualizacji", auto_now=True)

    class Meta:
        verbose_name = "Urządzenie"
        verbose_name_plural = "Urządzenia"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("device_detail", args=[self.pk])

    @property
    def is_critical(self):
        return self.importance == self.Importance.CRITICAL


class MonitoringResult(models.Model):
    """Wynik pojedynczego sprawdzenia dostępności urządzenia."""

    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name="monitoring_results",
        verbose_name="urządzenie",
    )
    checked_at = models.DateTimeField("data sprawdzenia", auto_now_add=True)
    is_available = models.BooleanField("urządzenie dostępne")
    response_time_ms = models.PositiveIntegerField(
        "czas odpowiedzi (ms)",
        blank=True,
        null=True,
    )
    error_message = models.CharField("komunikat błędu", max_length=255, blank=True)

    class Meta:
        verbose_name = "Wynik monitoringu"
        verbose_name_plural = "Wyniki monitoringu"
        ordering = ["-checked_at"]

    def __str__(self):
        return f"{self.device.name} - {'online' if self.is_available else 'offline'}"


class AdminCommand(models.Model):
    """Polecenie administracyjne odłączenia / przyłączenia urządzenia."""

    class CommandType(models.TextChoices):
        DISCONNECT = "disconnect", "Odłączenie od sieci"
        CONNECT = "connect", "Przyłączenie do sieci"

    class CommandStatus(models.TextChoices):
        PENDING = "pending", "Oczekuje na wykonanie"
        RUNNING = "running", "W trakcie"
        DONE = "done", "Wykonano"
        FAILED = "failed", "Niepowodzenie"
        CANCELLED = "cancelled", "Anulowano"

    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name="admin_commands",
        verbose_name="urządzenie",
    )
    command_type = models.CharField(
        "rodzaj polecenia",
        max_length=20,
        choices=CommandType.choices,
    )
    administrator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="admin_commands",
        verbose_name="administrator zlecający",
    )
    justification = models.TextField("uzasadnienie")
    status = models.CharField(
        "status wykonania",
        max_length=20,
        choices=CommandStatus.choices,
        default=CommandStatus.PENDING,
    )
    requested_at = models.DateTimeField("data zlecenia", auto_now_add=True)
    finished_at = models.DateTimeField("data zakończenia", blank=True, null=True)
    result_message = models.TextField("wynik", blank=True)
    error_message = models.TextField("komunikat błędu", blank=True)

    class Meta:
        verbose_name = "Polecenie administracyjne"
        verbose_name_plural = "Polecenia administracyjne"
        ordering = ["-requested_at"]

    def __str__(self):
        return f"{self.get_command_type_display()} - {self.device.name}"
