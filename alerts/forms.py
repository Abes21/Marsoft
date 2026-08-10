from django import forms

from .models import Alert, AlertNote


class AlertNoteForm(forms.ModelForm):
    """Formularz dodawania notatki do alertu."""

    class Meta:
        model = AlertNote
        fields = ["content"]
        widgets = {
            "content": forms.Textarea(attrs={"rows": 3, "placeholder": "Treść notatki..."}),
        }


class AlertStatusForm(forms.ModelForm):
    """Formularz zmiany statusu alertu."""

    class Meta:
        model = Alert
        fields = ["status", "assigned_to"]
        widgets = {
            "assigned_to": forms.Select(),
        }


class AlertFilterForm(forms.Form):
    """Formularz filtrowania alertów."""

    status = forms.ChoiceField(
        choices=[("", "Wszystkie statusy")] + Alert.Status.choices,
        required=False,
    )
    severity = forms.ChoiceField(
        choices=[("", "Wszystkie poziomy")] + Alert.Severity.choices,
        required=False,
    )
    device = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="Wszystkie urządzenia",
    )
    rule = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="Wszystkie reguły",
    )
    assigned_to = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="Wszyscy użytkownicy",
    )
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from devices.models import Device
        from .models import SecurityRule
        from accounts.models import User

        self.fields["device"].queryset = Device.objects.order_by("name")
        self.fields["rule"].queryset = SecurityRule.objects.order_by("name")
        self.fields["assigned_to"].queryset = User.objects.order_by("username")
