"""Bounded authorized retained metadata; no current-scope promotion or writes."""
import re
from django.views.decorators.http import require_GET
from .preparation_snapshots import assignment, authorized_history
from .staff_auth import staff_credential
from .staff_views import page, private_read, PAGE_SIZE
from .views import reply


@require_GET
def preparation_history(request,identity):
    if staff_credential(request,recent=True) is None:
        return private_read(reply({'error':'recent_staff_mfa_required'},403))
    before=None
    if request.GET:
        if set(request.GET)!={'before'} or len(request.GET.getlist('before'))!=1:
            return private_read(reply({'error':'invalid_cursor'},400))
        raw=request.GET['before']
        if re.fullmatch('[1-9][0-9]{0,9}',raw) is None or int(raw)>1000000000:
            return private_read(reply({'error':'invalid_cursor'},400))
        before=int(raw)
    grant=assignment(request,identity)
    if grant is None:return private_read(reply({'error':'not_found'},404))
    # Current-scope access is deliberately not substituted for retained access.
    rows=authorized_history(grant.quotation,grant)
    if before is not None:
        if not rows.filter(version=before).exists():return private_read(reply({'error':'not_found'},404))
        rows=rows.filter(version__lt=before)
    selected=list(rows.order_by('-version').values('version','business_version','review_version','created_at')[:PAGE_SIZE+1])
    items=selected[:PAGE_SIZE]
    older=items[-1]['version'] if len(selected)>PAGE_SIZE else None
    if 'text/html' in request.headers.get('Accept',''):
        return private_read(page(request,'access/preparation_history.html',
            {'identity':identity,'items':items,'older':older,'page_size':PAGE_SIZE}))
    return private_read(reply({'snapshots':items,'limit':PAGE_SIZE,'older':older}))
