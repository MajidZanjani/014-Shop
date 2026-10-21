"""Minimal health responses; readiness is intended for internal routing only."""
from django.db import DatabaseError, connection
from django.http import JsonResponse
from django.views.decorators.http import require_GET

@require_GET
def liveness(request):
    request.get_host()
    return JsonResponse({"status": "live"})

@require_GET
def readiness(request):
    request.get_host()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            if cursor.fetchone() != (1,):
                return JsonResponse({"status": "unavailable"}, status=503)
    except DatabaseError:
        return JsonResponse({"status": "unavailable"}, status=503)
    return JsonResponse({"status": "ready"})
