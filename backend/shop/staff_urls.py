from shop.payments.operation_views import queue as payment_queue,detail as payment_detail
from shop.payments.overpayment_views import queue as overpayment_queue,detail as overpayment_detail
from shop.catalog.support_refund_views import staff_refunds,staff_detail as staff_refund_detail
from shop.catalog.licence_change_views import staff_cases,staff_case
from shop.catalog.package_views import delivery_queue,delivery_page,delivery_control
from shop.catalog.support_views import staff_support_page
from shop.catalog.presentation import stylesheet
from django.urls import path
from shop.access import staff_auth, staff_views
from shop.access.archive_observation import reconciliation
from shop.access.request_evidence import evidence, capture_status
from shop.access.comparison_views import comparison
from shop.access.preparation_snapshots import snapshots, snapshot_detail
from shop.access.preparation_views import preparation
from shop.access.preparation_history import preparation_history
from shop.access.quotation_review import record_review
from shop.access.review_history import review_history
from shop.shb.staff_views import record_review as record_shb_review
from shop.shb.staff_orders import orders as shb_orders,detail as shb_order
urlpatterns=[
    path('staff/shb-orders/',shb_orders),
    path('staff/shb-orders/<uuid:identity>/',shb_order),
    path("staff/payments/",payment_queue),
    path("staff/payments/<int:identity>/",payment_detail),
    path("staff/overpayments/",overpayment_queue),
    path("staff/overpayments/<int:identity>/",overpayment_detail),
    path("staff/support-refunds/",staff_refunds),
    path("staff/support-refunds/<uuid:identity>/",staff_refund_detail),
    path('staff/licence-cases/',staff_cases),
    path('staff/licence-cases/<uuid:identity>/',staff_case),
    path('staff/delivery/',delivery_queue),
    path('staff/delivery/<uuid:identity>/',delivery_page),
    path('staff/delivery/<uuid:identity>/control/',delivery_control),
    path('staff/support/<uuid:identity>/',staff_support_page),
    path('purchase/assets/shop.css',stylesheet),
    path('staff/archive-intents/<uuid:identity>/claims/<uuid:claim_id>/reconciliation/',reconciliation),
    path('staff/',staff_auth.home),path('staff/session/',staff_auth.session_status),
    path('staff/login/',staff_auth.password_login),path('staff/verify/',staff_auth.verify),path('staff/logout/',staff_auth.sign_out),
    path('staff/quotation-requests/',staff_views.quotations),
    path('staff/quotation-requests/<uuid:identity>/',staff_views.quotation_detail),
    path('staff/quotation-requests/<uuid:identity>/reviews/',record_review),
    path('staff/quotation-requests/<uuid:identity>/shb-reviews/',record_shb_review),
    path('staff/quotation-requests/<uuid:identity>/reviews/history/',review_history),
    path('staff/quotation-requests/<uuid:identity>/request-evidence/<int:version>/',evidence),
    path('staff/quotation-requests/<uuid:identity>/request-evidence/<int:version>/status/',capture_status),
    path('staff/quotation-requests/<uuid:identity>/preparation-snapshots/',snapshots),
    path('staff/quotation-requests/<uuid:identity>/preparation-snapshots/history/',preparation_history),
    path('staff/quotation-requests/<uuid:identity>/preparation-snapshots/<int:version>/compare/',comparison),
    path('staff/quotation-requests/<uuid:identity>/preparation-snapshots/<int:version>/',snapshot_detail),
    path('staff/quotation-requests/<uuid:identity>/preparation/',preparation),
    path('staff/quotation-requests/<uuid:identity>/business/',staff_views.quotation_business),
]
