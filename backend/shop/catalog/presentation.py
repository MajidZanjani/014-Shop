"""Public fixed stylesheet and non-sensitive customer navigation context."""
from pathlib import Path
from django.http import HttpResponse
from django.views.decorators.http import require_GET
CSS = Path(__file__).with_name('shop.css').read_text()


@require_GET
def stylesheet(request):
    response = HttpResponse(CSS, content_type='text/css; charset=utf-8')
    response['Cache-Control'] = 'public, max-age=3600'
    response['X-Content-Type-Options'] = 'nosniff'
    return response


def customer_navigation(request):
    path = request.path
    step = ('payment' if path.endswith('/payment/') else 'review' if '/checkout-rehearsal/' in path
            else 'business' if '/business/' in path else 'cart' if '/cart/' in path else 'access')
    return {'shop_step': step}
