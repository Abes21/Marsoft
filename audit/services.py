from core.middleware import get_current_request

from .models import ActivityLog


def get_client_ip(request):
    if request is None:
        return None
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def log_action(action_type, description, user=None, username=None, request=None):
    """Zapisuje działanie; użytkownika i IP dobiera z aktualnego żądania."""

    if request is None:
        request = get_current_request()

    if (
        user is None
        and request is not None
        and getattr(request, "user", None)
        and request.user.is_authenticated
    ):
        user = request.user

    ActivityLog.objects.create(
        user=user,
        username=username or (user.username if user else ""),
        action_type=action_type,
        description=description,
        ip_address=get_client_ip(request),
    )
