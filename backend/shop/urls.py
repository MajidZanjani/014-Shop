from django.urls import path
from shop.core.health import liveness, readiness
from shop.catalog.views import catalog, validate, save_draft, get_draft
from shop.catalog.simple import simple_purchase
from shop.access.views import session_status, request_code, verify_code, sign_out
from shop.catalog.cart_views import current_cart
from shop.catalog.quotation_views import quotations, quotation_detail
urlpatterns = [path("api/v1/quotation-requests/", quotations), path("api/v1/quotation-requests/<uuid:identity>/", quotation_detail), path("api/v1/cart/", current_cart), path("api/v1/customer/session/", session_status), path("api/v1/customer/request-code/", request_code), path("api/v1/customer/verify/", verify_code), path("api/v1/customer/logout/", sign_out), path("purchase/simple/", simple_purchase), path("api/v1/configuration-drafts/", save_draft), path("api/v1/configuration-drafts/<uuid:identity>/", get_draft), path("api/v1/catalog/", catalog), path("api/v1/configurations/validate/", validate), path("health/live", liveness), path("health/ready", readiness)]
