import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import User
from alerts.models import Alert, AlertHistory, AlertNote, SecurityRule
from devices.models import Device, MonitoringResult
from logs.models import LogEntry
from notifications.models import Notification


class Command(BaseCommand):
    help = "Generuje dane demonstracyjne: 100 urządzeń, 100k logów, 5k alertów (RF-44)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Wyczyść bazę z danych demo przed seedowaniem (ostrożnie!)",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            self.stdout.write(self.style.WARNING("Czyszczę bazę z danych demo..."))
            Notification.objects.all().delete()
            AlertHistory.objects.all().delete()
            AlertNote.objects.all().delete()
            Alert.objects.all().delete()
            LogEntry.objects.all().delete()
            MonitoringResult.objects.all().delete()
            Device.objects.all().delete()

        self.create_devices()
        self.create_logs()
        self.create_alerts()
        self.stdout.write(self.style.SUCCESS("Seedowanie zakończone."))

    # ===== URZĄDZENIA =====
    def create_devices(self):
        self.stdout.write("Tworzę urządzenia...")

        departments = ["IT", "Księgowość", "HR", "Sprzedaż", "Produkcja", "Zarząd", "Logistyka"]
        locations = ["Budynek A - 1 piętro", "Budynek A - 2 piętro", "Budynek B", "Serwerownia", "Magazyn"]
        os_list = ["Windows 11", "Windows 10", "Ubuntu 22.04", "Ubuntu 24.04", "Debian 12", "macOS Sonoma"]

        device_types = [
            (Device.DeviceType.COMPUTER, 30),
            (Device.DeviceType.LAPTOP, 35),
            (Device.DeviceType.SERVER, 10),
            (Device.DeviceType.PRINTER, 8),
            (Device.DeviceType.ROUTER, 5),
            (Device.DeviceType.SWITCH, 7),
            (Device.DeviceType.MOBILE, 5),
        ]

        created = 0
        for dtype, count in device_types:
            prefix = {
                "computer": "PC",
                "laptop": "LT",
                "server": "SRV",
                "printer": "PRT",
                "router": "RTR",
                "switch": "SW",
                "mobile": "MOB",
            }[dtype]

            for i in range(1, count + 1):
                # Unikaj kolizji IP
                while True:
                    ip = f"10.0.{random.randint(1, 10)}.{random.randint(1, 254)}"
                    if not Device.objects.filter(ip_address=ip).exists():
                        break

                importance = random.choice(
                    [Device.Importance.LOW, Device.Importance.STANDARD,
                     Device.Importance.HIGH, Device.Importance.CRITICAL]
                )

                # Serwery zawsze wysokie/krytyczne
                if dtype == "server":
                    importance = random.choice([Device.Importance.HIGH, Device.Importance.CRITICAL])

                Device.objects.create(
                    name=f"{prefix}-{i:03d}",
                    device_type=dtype,
                    ip_address=ip,
                    mac_address=":".join([f"{random.randint(0, 255):02x}" for _ in range(6)]),
                    operating_system=random.choice(os_list) if dtype in ("computer", "laptop", "server") else "",
                    assigned_user=f"user{i:03d}" if dtype in ("computer", "laptop", "mobile") else "",
                    department=random.choice(departments),
                    location=random.choice(locations),
                    importance=importance,
                    monitoring_status=random.choice([
                        Device.MonitoringStatus.ONLINE,
                        Device.MonitoringStatus.ONLINE,
                        Device.MonitoringStatus.ONLINE,
                        Device.MonitoringStatus.OFFLINE,
                        Device.MonitoringStatus.UNKNOWN,
                    ]),
                    network_access_status=random.choice([
                        Device.NetworkAccessStatus.CONNECTED,
                        Device.NetworkAccessStatus.CONNECTED,
                        Device.NetworkAccessStatus.CONNECTED,
                        Device.NetworkAccessStatus.DISCONNECTED_ADMIN,
                    ]),
                    monitoring_enabled=True,
                    disconnect_blocked=(dtype == "server" and importance == "critical"),
                )
                created += 1

        self.stdout.write(self.style.SUCCESS(f"  Utworzono {created} urządzeń."))

    # ===== LOGI =====
    def create_logs(self):
        self.stdout.write("Tworzę 100 000 logów (bulk_create)...")

        devices = list(Device.objects.all())
        if not devices:
            self.stderr.write("  Brak urządzeń - pomijam logi.")
            return

        sources = ["system", "firewall", "antivirus", "backup", "vpn", "auth", "web", "mail", "db"]
        event_types = ["auth", "network", "service", "access", "update", "error", "scan"]
        users_pool = [f"user{i:03d}" for i in range(1, 50)] + ["admin", "sysadmin", "backup_svc"]

        now = timezone.now()
        logs_to_create = []

        for i in range(100_000):
            # Rozkład: 70% info, 15% warning, 10% error, 5% critical
            r = random.random()
            if r < 0.70:
                level = "info"
            elif r < 0.85:
                level = "warning"
            elif r < 0.95:
                level = "error"
            else:
                level = "critical"

            source = random.choice(sources)
            event_type = random.choice(event_types)

            # Realistyczne komunikaty
            if event_type == "auth":
                if random.random() < 0.7:
                    message = f"Nieudane logowanie użytkownika {random.choice(users_pool)}"
                else:
                    message = f"Udane logowanie użytkownika {random.choice(users_pool)}"
            elif event_type == "network":
                message = f"Połączenie {random.choice(['przychodzące', 'wychodzące'])} na porcie {random.randint(80, 65535)}"
            elif event_type == "service":
                message = f"Usługa {random.choice(['backup', 'apache', 'postgres', 'redis'])} {random.choice(['uruchomiona', 'zatrzymana', 'zrestartowana'])}"
            elif event_type == "scan":
                message = "Wykryto skanowanie portów"
            else:
                message = f"Zdarzenie systemowe nr {i}"

            # Data: losowa z ostatnich 30 dni, z naciskiem na ostatnie 7 dni
            hours_ago = random.expovariate(1 / (24 * 7))
            hours_ago = min(hours_ago, 24 * 30)
            event_time = now - timedelta(hours=hours_ago)

            device = random.choice(devices) if random.random() < 0.8 else None

            logs_to_create.append(
                LogEntry(
                    event_time=event_time,
                    source=source,
                    device=device,
                    user=random.choice(users_pool) if event_type == "auth" else "",
                    event_type=event_type,
                    level=level,
                    message=message,
                )
            )

            # Zapisuj co 10 000
            if len(logs_to_create) >= 10_000:
                LogEntry.objects.bulk_create(logs_to_create, batch_size=1000)
                logs_to_create = []
                self.stdout.write(f"  Zapisano {(i + 1)} / 100000")

        if logs_to_create:
            LogEntry.objects.bulk_create(logs_to_create, batch_size=1000)

        self.stdout.write(self.style.SUCCESS("  Utworzono 100 000 logów."))

    # ===== ALERTY =====
    def create_alerts(self):
        self.stdout.write("Tworzę 5000 alertów...")

        devices = list(Device.objects.all())
        rules = list(SecurityRule.objects.filter(is_active=True))
        admins = list(User.objects.filter(role=User.Role.ADMIN))

        if not rules:
            self.stderr.write("  Brak reguł - tworzę domyślne...")
            from django.core.management import call_command
            call_command("create_default_rules")
            rules = list(SecurityRule.objects.filter(is_active=True))

        alert_templates = [
            "Wielokrotne nieudane logowanie ({n} prób)",
            "Zdarzenie krytyczne: {src}",
            "Logowanie administratora: {user}",
            "Niedostępność urządzenia krytycznego: {dev}",
            "Wykryto skanowanie portów z adresu {ip}",
            "Nietypowa aktywność użytkownika {user}",
            "Przekroczono limit połączeń na urządzeniu {dev}",
            "Wygasł certyfikat SSL na {dev}",
        ]

        now = timezone.now()
        alerts_to_create = []

        for i in range(5_000):
            rule = random.choice(rules) if rules else None
            device = random.choice(devices) if random.random() < 0.7 else None

            template = random.choice(alert_templates)
            name = template.format(
                n=random.randint(5, 20),
                src=random.choice(["firewall", "antivirus", "system", "backup"]),
                user=random.choice(["admin", "sysadmin"]),
                dev=device.name if device else "SRV-001",
                ip=f"10.0.{random.randint(1, 10)}.{random.randint(1, 254)}",
            )

            # Rozkład statusów
            r = random.random()
            if r < 0.60:
                status = Alert.Status.RESOLVED
            elif r < 0.75:
                status = Alert.Status.NEW
            elif r < 0.85:
                status = Alert.Status.IN_PROGRESS
            elif r < 0.95:
                status = Alert.Status.IGNORED
            else:
                status = Alert.Status.FALSE_POSITIVE

            severity = random.choice([
                Alert.Severity.LOW,
                Alert.Severity.MEDIUM,
                Alert.Severity.MEDIUM,
                Alert.Severity.HIGH,
                Alert.Severity.CRITICAL,
            ])

            hours_ago = random.expovariate(1 / (24 * 5))
            hours_ago = min(hours_ago, 24 * 30)
            created_at = now - timedelta(hours=hours_ago)

            resolved_at = None
            if status == Alert.Status.RESOLVED:
                resolved_at = created_at + timedelta(hours=random.uniform(0.5, 72))

            alerts_to_create.append(
                Alert(
                    name=name,
                    description=f"Automatycznie wygenerowany alert #{i + 1}",
                    severity=severity,
                    status=status,
                    rule=rule,
                    device=device,
                    assigned_to=random.choice(admins) if admins and status != Alert.Status.NEW else None,
                    created_at=created_at,
                    resolved_at=resolved_at,
                )
            )

            if len(alerts_to_create) >= 500:
                Alert.objects.bulk_create(alerts_to_create, batch_size=200)
                alerts_to_create = []
                self.stdout.write(f"  Zapisano {i + 1} / 5000")

        if alerts_to_create:
            Alert.objects.bulk_create(alerts_to_create, batch_size=200)

        self.stdout.write(self.style.SUCCESS("  Utworzono 5000 alertów."))
