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
        return response
