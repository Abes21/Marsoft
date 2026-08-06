from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'status', 'is_active')
    list_filter = ('role', 'status', 'is_active')

    fieldsets = UserAdmin.fieldsets + (
        ('Rola i status', {'fields': ('role', 'status')}),
    )
