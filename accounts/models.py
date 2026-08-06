from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Własny użytkownik z rolą i statusem konta."""

    class Role(models.TextChoices):
        ADMIN = 'admin', 'Administrator'
        OPERATOR = 'operator', 'Operator'

    class AccountStatus(models.TextChoices):
        ACTIVE = 'active', 'Aktywne'
        BLOCKED = 'blocked', 'Zablokowane'

    email = models.EmailField('adres e-mail', unique=True)
    role = models.CharField(
        'rola',
        max_length=20,
        choices=Role.choices,
        default=Role.OPERATOR,
    )
    status = models.CharField(
        'status konta',
        max_length=20,
        choices=AccountStatus.choices,
        default=AccountStatus.ACTIVE,
    )

    def is_admin_role(self) -> bool:
        return self.role == self.Role.ADMIN

    def is_operator_role(self) -> bool:
        return self.role == self.Role.OPERATOR

    def is_blocked(self) -> bool:
        return self.status == self.AccountStatus.BLOCKED

    def __str__(self) -> str:
        return self.username
