from shop.catalog.support_refund_views import refunds,detail as refund_detail
from shop.catalog.licence_change_views import case_list,new_case,case_detail
from shop.catalog.package_views import package_page,package_access,package_download
from shop.catalog.support_views import support_page
from django.urls import path
from shop.core.health import liveness, readiness
from shop.catalog.views import catalog, validate, save_draft, get_draft
from shop.catalog.simple import simple_purchase
from shop.access.customer_portal import customer_access
from shop.access.views import session_status, request_code, verify_code, sign_out
from shop.catalog.cart_editor import cart_editor
from shop.catalog.cart_views import current_cart
from shop.catalog.quotation_capture import quotation_capture
from shop.catalog.quotation_views import quotations, quotation_detail
from shop.catalog.quotation_history import quotation_history
from shop.catalog.timeline_views import quotation_timeline
from shop.catalog.document_views import document_preview
from shop.catalog.business_views import business_editor
from shop.catalog.business_binding_views import bind_business
from shop.catalog.checkout_views import checkout_api, checkout_page
from shop.catalog.checkout_payment_views import payment_page, payment_api
from shop.catalog.presentation import stylesheet
urlpatterns = [
    path("purchase/checkout-rehearsal/<uuid:identity>/support/refunds/",refunds),
    path("purchase/checkout-rehearsal/<uuid:identity>/support/refunds/<uuid:case_id>/",refund_detail),
    path('purchase/checkout-rehearsal/<uuid:identity>/changes/',case_list),
    path('purchase/checkout-rehearsal/<uuid:identity>/changes/new/<uuid:line_id>/',new_case),
    path('purchase/checkout-rehearsal/<uuid:identity>/changes/<uuid:case_id>/',case_detail),
    path('purchase/checkout-rehearsal/<uuid:identity>/packages/',package_page),
    path('purchase/checkout-rehearsal/<uuid:identity>/packages/<uuid:package_id>/access/',package_access),
    path('purchase/checkout-rehearsal/<uuid:identity>/packages/<uuid:package_id>/download/',package_download),
    path('purchase/checkout-rehearsal/<uuid:identity>/support/',support_page),path("purchase/assets/shop.css", stylesheet), path("purchase/checkout-rehearsal/<uuid:identity>/payment/", payment_page), path("api/v1/checkout-rehearsal/<uuid:identity>/payment/", payment_api), path("purchase/checkout-rehearsal/", checkout_page), path("api/v1/checkout-rehearsal/", checkout_api), path("purchase/request-quotation/", quotation_capture), path("purchase/cart/", cart_editor), path("purchase/quotations/", quotation_history), path("purchase/access/", customer_access), path("purchase/quotation-timeline/<uuid:identity>/", quotation_timeline), path("purchase/quotation-documents/<uuid:identity>/", document_preview), path("purchase/quotation-business/<uuid:identity>/", bind_business), path("purchase/business/", business_editor), path("api/v1/quotation-requests/", quotations), path("api/v1/quotation-requests/<uuid:identity>/", quotation_detail), path("api/v1/cart/", current_cart), path("api/v1/customer/session/", session_status), path("api/v1/customer/request-code/", request_code), path("api/v1/customer/verify/", verify_code), path("api/v1/customer/logout/", sign_out), path("purchase/simple/", simple_purchase), path("api/v1/configuration-drafts/", save_draft), path("api/v1/configuration-drafts/<uuid:identity>/", get_draft), path("api/v1/catalog/", catalog), path("api/v1/configurations/validate/", validate), path("health/live", liveness), path("health/ready", readiness)]
