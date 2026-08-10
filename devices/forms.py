from django import forms

from .models import Device


class DeviceForm(forms.ModelForm):
    """Formularz dodawania i edycji urządzenia."""

    class Meta:
        model = Device
        fields = [
            "name",
            "device_type",
            "ip_address",
            "mac_address",
            "operating_system",
            "assigned_user",
            "department",
            "location",
            "importance",
            "monitoring_status",
            "network_access_status",
            "monitoring_enabled",
            "notes",
        ]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 4}),
        }


class AdminCommandForm(forms.Form):
    """Formularz potwierdzenia operacji odłączenia / przyłączenia."""

    justification = forms.CharField(
        label="Uzasadnienie operacji",
        widget=forms.Textarea(attrs={"rows": 3}),
        min_length=5,
        max_length=500,
        error_messages={
            "required": "Uzasadnienie jest wymagane.",
            "min_length": "Uzasadnienie musi mieć co najmniej 5 znaków.",
            "max_length": "Uzasadnienie może mieć maksymalnie 500 znaków.",
        },
    )
