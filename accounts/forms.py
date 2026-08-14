from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User


class AdminUserCreateForm(UserCreationForm):
    """Tworzenie konta przez administratora (RF-06)."""

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name", "role"]


class AdminUserEditForm(forms.ModelForm):
    """Edycja danych i roli konta (RF-06)."""

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "role"]
