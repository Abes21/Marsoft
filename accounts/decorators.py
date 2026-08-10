from functools import wraps

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


def admin_required(view_func):
    """Dostęp tylko dla użytkownika z rolą administratora."""

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(settings.LOGIN_URL)

        if not request.user.is_admin_role():
            raise PermissionDenied

        return view_func(request, *args, **kwargs)

    return _wrapped_view
