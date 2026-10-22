"""Validate Host for every route, including public and authenticated product APIs."""
class ValidHostMiddleware:
    def __init__(self,get_response): self.get_response=get_response
    def __call__(self,request):
        request.get_host()
        return self.get_response(request)
