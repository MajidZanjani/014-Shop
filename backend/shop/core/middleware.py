"""Validate Host for every route, including public and authenticated product APIs."""
class ValidHostMiddleware:
    def __init__(self,get_response): self.get_response=get_response
    def __call__(self,request):
        request.get_host()
        return self.get_response(request)


class FormReferrerPolicyMiddleware:
    """Keep same-origin HTML forms usable without leaking referrers to other origins.

    Fetch navigation POSTs under no-referrer carry Origin:null, which CSRF must
    reject. Read-only documents and JSON keep their existing restrictive policy.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        directives = response.get('Content-Security-Policy', '').split(';')
        if (response.get('Content-Type', '').split(';')[0] == 'text/html'
                and any(part.strip() == "form-action 'self'" for part in directives)):
            response['Referrer-Policy'] = 'same-origin'
            if not any(part.strip().startswith('style-src ') for part in directives):
                response['Content-Security-Policy'] += "; style-src 'self'"
        return response


class CustomerAccessContextMiddleware:
    """Opaque response comparison only; never a credential or authorization input."""
    def __init__(self,get_response):self.get_response=get_response

    def __call__(self,request):
        response=self.get_response(request)
        path=request.path
        if (path.startswith('/api/v1/customer/') or path=='/api/v1/cart/'
                or path.startswith('/api/v1/configuration-drafts/')
                or path.startswith('/api/v1/quotation-requests/')):
            import json
            from django.utils.crypto import salted_hmac
            user=request.user
            value=json.dumps([request.session.session_key,
                              str(user.pk) if user.is_authenticated else None,
                              request.session.get('shop_verified_identity')],separators=(',',':'))
            response['X-Shop-Access-Context']=salted_hmac(
                'shop.customer.response-context.v1',value,algorithm='sha256').hexdigest()
            response['Cache-Control']='no-store'
        return response
