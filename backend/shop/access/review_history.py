"""Assigned internal decision metadata, without private scope hashes or MFA."""
from django.views.decorators.http import require_GET
from shop.catalog.models import REVIEW_DECISIONS
from .preparation_snapshots import assignment
from .quotation_review import history_rows
from .staff_auth import staff_credential
from .staff_views import page, private_read, before_version, PAGE_SIZE
from .views import reply


@require_GET
def review_history(request,identity):
    if staff_credential(request,recent=True) is None:
        return private_read(reply({'error':'recent_staff_mfa_required'},403))
    try:before=before_version(request.GET)
    except ValueError:return private_read(reply({'error':'invalid_cursor'},400))
    grant=assignment(request,identity)
    if grant is None:return private_read(reply({'error':'not_found'},404))
    rows=history_rows(grant.quotation)
    if before is not None:
        if not rows.filter(version=before).exists():return private_read(reply({'error':'not_found'},404))
        rows=rows.filter(version__lt=before)
    selected=list(rows.values('version','business_version','decision','reviewer_id','created_at')[:PAGE_SIZE+1])
    items=selected[:PAGE_SIZE]
    for row in items:
        row['label']=dict(REVIEW_DECISIONS)[row['decision']]
        row['reviewer_id']=str(row['reviewer_id'])
    older=items[-1]['version'] if len(selected)>PAGE_SIZE else None
    if 'text/html' in request.headers.get('Accept',''):
        return private_read(page(request,'access/review_history.html',
            {'identity':identity,'items':items,'older':older,'page_size':PAGE_SIZE}))
    return private_read(reply({'reviews':items,'limit':PAGE_SIZE,'older':older}))
