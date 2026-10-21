from django.urls import path
from shop.core.health import liveness, readiness
urlpatterns = [path("health/live", liveness), path("health/ready", readiness)]
