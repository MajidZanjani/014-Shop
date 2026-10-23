from django.urls import path
from shop.access import staff_auth, staff_views
from shop.access.quotation_review import record_review
urlpatterns=[
    path('staff/',staff_auth.home),path('staff/session/',staff_auth.session_status),
    path('staff/login/',staff_auth.password_login),path('staff/verify/',staff_auth.verify),path('staff/logout/',staff_auth.sign_out),
    path('staff/quotation-requests/',staff_views.quotations),
    path('staff/quotation-requests/<uuid:identity>/',staff_views.quotation_detail),
    path('staff/quotation-requests/<uuid:identity>/reviews/',record_review),
]
