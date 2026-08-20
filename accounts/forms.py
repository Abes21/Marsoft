from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User


class AdminUserCreateForm(UserCreationForm):
    """Tworzenie konta przez administratora (RF-06)."""

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'np. jan.kowalski@firma.pl'}),
    )

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name", "role"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dodaj klasy CSS do pól
        for field_name, field in self.fields.items():
            if field_name in ('password1', 'password2'):
                field.widget.attrs.update({'class': 'form-input'})
            elif field_name == 'role':
                field.widget.attrs.update({'class': 'form-select'})
            elif field_name not in ('email',):
                field.widget.attrs.update({'class': 'form-input'})


class AdminUserEditForm(forms.ModelForm):
    """Edycja danych i roli konta (RF-06)."""

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "role"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name == 'role':
                field.widget.attrs.update({'class': 'form-select'})
            else:
                field.widget.attrs.update({'class': 'form-input'})
