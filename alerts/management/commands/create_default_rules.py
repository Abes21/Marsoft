from django.core.management.base import BaseCommand

from alerts.models import SecurityRule


class Command(BaseCommand):
    help = "Tworzy domyślne reguły bezpieczeństwa"

    def handle(self, *args, **options):
        rules_data = [
            {
                "name": "Wielokrotne nieudane logowanie",
                "description": "Wykrywa 5 lub więcej nieudanych prób logowania w ciągu 10 minut.",
                "rule_type": SecurityRule.RuleType.FAILED_LOGIN,
                "threshold": 5,
                "time_window_minutes": 10,
                "severity": SecurityRule.Severity.HIGH,
            },
            {
                "name": "Zdarzenie krytyczne",
                "description": "Tworzy alert po otrzymaniu logu o poziomie krytycznym.",
                "rule_type": SecurityRule.RuleType.CRITICAL_EVENT,
                "threshold": 1,
                "time_window_minutes": 1,
                "severity": SecurityRule.Severity.CRITICAL,
            },
            {
                "name": "Logowanie administratora",
                "description": "Wykrywa logowanie na konto z uprawnieniami administracyjnymi.",
                "rule_type": SecurityRule.RuleType.ADMIN_LOGIN,
                "threshold": 1,
                "time_window_minutes": 1,
                "severity": SecurityRule.Severity.MEDIUM,
            },
            {
                "name": "Niedostępność urządzenia krytycznego",
                "description": "Tworzy alert, gdy urządzenie krytyczne jest niedostępne przez 3 kolejne sprawdzenia.",
                "rule_type": SecurityRule.RuleType.DEVICE_UNAVAILABLE,
                "threshold": 3,
                "time_window_minutes": 15,
                "severity": SecurityRule.Severity.HIGH,
            },
        ]

        created_count = 0
        for rule_data in rules_data:
            rule, created = SecurityRule.objects.get_or_create(
                name=rule_data["name"],
                defaults=rule_data,
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Utworzono regułę: {rule.name}"))
            else:
                self.stdout.write(f"Reguła już istnieje: {rule.name}")

        self.stdout.write(self.style.SUCCESS(f"Utworzono {created_count} nowych reguł."))
