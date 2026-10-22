from django.urls import path
from shop.core.health import liveness, readiness
from shop.catalog.views import catalog, validate, save_draft, get_draft
from shop.catalog.simple import simple_purchase
urlpatterns = [path("purchase/simple/", simple_purchase), path("api/v1/configuration-drafts/", save_draft), path("api/v1/configuration-drafts/<uuid:identity>/", get_draft), path("api/v1/catalog/", catalog), path("api/v1/configurations/validate/", validate), path("health/live", liveness), path("health/ready", readiness)]
