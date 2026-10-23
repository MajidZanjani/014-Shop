"""Separate staff app namespace: never trust customer hosts or password-only sessions."""
from .staff_auth import enabled, staff_credential
from .views import reply

class StaffHostMiddleware:
    def __init__(self,get_response):self.get_response=get_response
    def __call__(self,request):
        if not enabled(request):return reply({'error':'not_found'},404)
        return self.get_response(request)

class StaffMFAMiddleware:
    PUBLIC={'/staff/','/staff/session/','/staff/login/','/staff/verify/','/staff/logout/'}
    def __init__(self,get_response):self.get_response=get_response
    def __call__(self,request):
        if request.path.startswith('/admin'):return reply({'error':'not_found'},404)
        if request.path not in self.PUBLIC and staff_credential(request,recent=True) is None:
            return reply({'error':'recent_staff_mfa_required'},403)
        return self.get_response(request)
