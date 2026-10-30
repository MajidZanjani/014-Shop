"""SHB release boundary: invitations protect content; old new-sale routes close."""
from django.conf import settings
from django.http import HttpResponse
from django.middleware.csrf import CsrfViewMiddleware
from shop.access.recovery import recovery_held
from .invitations import current

PROTECTED={'/','/shop/','/support/','/purchase/simple/','/api/v1/catalog/','/api/v1/shb/catalog/','/shop/assets/shop.css'}
OLD_SALES={'/api/v1/configurations/validate/','/api/v1/cart/','/purchase/cart/','/purchase/checkout-rehearsal/','/api/v1/checkout-rehearsal/','/purchase/request-quotation/'}


def denied(status=403):
    response=HttpResponse('Access requires a current SLL invitation. Contact SLL for assistance.',status=status,content_type='text/plain; charset=utf-8')
    response['Cache-Control']='no-store';response['Referrer-Policy']='no-referrer'
    response['Content-Security-Policy']="default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
    return response


class ShopGateMiddleware:
    def __init__(self,get_response):self.get_response=get_response

    def __call__(self,request):
        path=request.path
        old_post=request.method not in ('GET','HEAD') and path.startswith(('/api/v1/configuration-drafts/','/api/v1/quotation-requests/','/purchase/checkout-rehearsal/','/api/v1/checkout-rehearsal/'))
        time_panel=('/checkout-rehearsal/' in path and '/support/' in path) or path.startswith('/staff/support/')
        if path in OLD_SALES or old_post or time_panel:return denied(404)
        protected=path in PROTECTED or path.startswith(('/invite/','/shop/private/','/_astro/'))
        if protected:
            request.shb_protected=True
            if request.get_host().split(':')[0] not in ('shop.xspi.pro','localhost','127.0.0.1'):
                return denied(404)
            if not request.is_secure() and not (getattr(settings,'SHB_ALLOW_LOOPBACK_HTTP',False)
                    and request.get_host().split(':')[0] in ('127.0.0.1','localhost')):
                return denied()
            if recovery_held():return denied(503)
            if not path.startswith('/invite/'):
                request.shb_invitation=current(request)
                if request.shb_invitation is None:return denied()
        response=self.get_response(request)
        if protected:
            response['Cache-Control']='no-store';response['Referrer-Policy']='no-referrer'
            response['Vary']='Cookie'
        return response


class ShopCsrfViewMiddleware(CsrfViewMiddleware):
    def _origin_verified(self,request):
        # Native forms with no-referrer can carry Origin:null. Accept that case
        # only with browser-enforced same-origin Fetch Metadata on the exact SHB
        # form route. Django still requires its normal matching cookie/form CSRF
        # token. Null/missing/foreign metadata never grants this exception.
        if (getattr(request,'shb_protected',False) and request.path=='/purchase/simple/'
                and request.META.get('HTTP_ORIGIN')=='null'
                and request.META.get('HTTP_SEC_FETCH_SITE')=='same-origin'):
            return True
        return super()._origin_verified(request)
