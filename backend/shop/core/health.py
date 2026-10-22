"""Minimal health responses; readiness is intended for internal routing only."""
from django.db import DatabaseError, connection
from .logging import safe_event
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
@require_GET
def liveness(request):
    request.get_host()
    safe_event("health.live", 200)
    return JsonResponse({"status": "live"})

@csrf_exempt
@require_GET
def readiness(request):
    request.get_host()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            if cursor.fetchone() != (1,):
                safe_event("health.ready", 503)
                return JsonResponse({"status": "unavailable"}, status=503)
    except DatabaseError:
        safe_event("health.ready", 503)
        return JsonResponse({"status": "unavailable"}, status=503)
    safe_event("health.ready", 200)
    return JsonResponse({"status": "ready"})
