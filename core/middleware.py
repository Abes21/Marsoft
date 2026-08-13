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
