from django.conf import settings
from django.http import HttpResponse


class SimpleCORSMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if self._is_preflight_request(request):
            response = HttpResponse(status=204)
        else:
            response = self.get_response(request)

        return self._apply_cors_headers(request, response)

    def _is_preflight_request(self, request) -> bool:
        return (
            request.method == "OPTIONS"
            and self._is_allowed_origin(request.headers.get("Origin"))
            and request.path.startswith("/api/")
            and bool(request.headers.get("Access-Control-Request-Method"))
        )

    def _is_allowed_origin(self, origin: str | None) -> bool:
        return bool(origin) and origin in settings.CORS_ALLOWED_ORIGINS

    def _apply_cors_headers(self, request, response):
        origin = request.headers.get("Origin")

        if not self._is_allowed_origin(origin) or not request.path.startswith("/api/"):
            return response

        response["Access-Control-Allow-Origin"] = origin
        response["Vary"] = "Origin"
        response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = request.headers.get(
            "Access-Control-Request-Headers",
            "Content-Type, Accept, Origin",
        )
        response["Access-Control-Max-Age"] = "86400"
        return response
