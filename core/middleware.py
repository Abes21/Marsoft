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
