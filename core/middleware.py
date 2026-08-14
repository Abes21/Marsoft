import threading

_request_local = threading.local()


def get_current_request():
    """Zwraca aktualne żądanie HTTP (do użytku w sygnałach)."""
    return getattr(_request_local, "request", None)


class CurrentRequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _request_local.request = request
        try:
            return self.get_response(request)
        finally:
            _request_local.request = None


from django.core.cache import cache
from django.http import HttpResponse


class LoginRateLimitMiddleware:
    """Ochrona logowania przed brute force (RNF-12)."""

    MAX_PER_USER = 5
    MAX_PER_IP = 10
    WINDOW_SECONDS = 300

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == "POST" and request.path.endswith("/login/"):
            username = str(request.POST.get("username", ""))[:150]
            ip = get_client_ip(request) or "unknown"

            user_key = f"login_fail_user:{username}"
            ip_key = f"login_fail_ip:{ip}"

            if (
                cache.get(user_key, 0) >= self.MAX_PER_USER
                or cache.get(ip_key, 0) >= self.MAX_PER_IP
            ):
                from audit.services import log_action

                log_action(
                    "login_failed",
                    f"Zablokowano próby logowania (brute force) dla „{username}”",
                    username=username,
                )
                return HttpResponse(
                    "Zbyt wiele nieudanych prób logowania. "
                    "Spróbuj ponownie za 5 minut.",
                    status=429,
                )

            response = self.get_response(request)

            if response.status_code == 302:
                # udane logowanie - zerujemy liczniki
                cache.delete(user_key)
                cache.delete(ip_key)
            else:
                cache.set(user_key, cache.get(user_key, 0) + 1, self.WINDOW_SECONDS)
                cache.set(ip_key, cache.get(ip_key, 0) + 1, self.WINDOW_SECONDS)

            return response

        return self.get_response(request)


from datetime import datetime

from django.utils import timezone


class SessionTimeoutMiddleware:
    """Automatyczne wylogowanie po okresie nieaktywności (RF-05)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            from django.conf import settings as dj_settings
            from django.contrib import messages as dj_messages
            from django.contrib.auth import logout as dj_logout

            timeout = getattr(dj_settings, "SESSION_IDLE_TIMEOUT_SECONDS", 1800)
            now = timezone.now()
            last = request.session.get("last_activity")

            if last:
                try:
                    last_dt = datetime.fromisoformat(last)
                except ValueError:
                    last_dt = now

                if (now - last_dt).total_seconds() > timeout:
                    dj_messages.info(request, "Sesja wygasła z powodu nieaktywności.")
                    dj_logout(request)
                    return self.get_response(request)

            request.session["last_activity"] = now.isoformat()

        return self.get_response(request)


def get_client_ip(request):
    """Zwraca adres IP klienta (X-Forwarded-For lub REMOTE_ADDR)."""

    if request is None:
        return None

    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()

    return request.META.get("REMOTE_ADDR")
