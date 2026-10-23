"""Bounded customer projection of immutable event metadata only."""
import re
from urllib.parse import urlencode
from .models import QuotationBusinessScope, QuotationReview
from .quotation_status import LABELS, customer_review_status

PAGE_SIZE = 20
DECISIONS = {'needs_information', 'ready_for_commercial_review', 'declined'}


def cursors(query, quotation):
    limits = {'scope_before': quotation.business_version + 1, 'review_before': quotation.review_version + 1}
    if not query:
        return limits
    if set(query) != set(limits):
        raise ValueError('cursor fields')
    result = {}
    for name, maximum in limits.items():
        values = query.getlist(name)
        if len(values) != 1 or re.fullmatch(r'0|[1-9][0-9]{0,9}', values[0]) is None:
            raise ValueError('cursor')
        value = int(values[0])
        if value > maximum:
            raise ValueError('future cursor')
        result[name] = value
    return result


def timeline_events(quotation, before):
    # Parent counters are committed with each append. Reading that immutable prefix
    # avoids mixing later writes into this response, without locking out writers.
    scopes = QuotationBusinessScope.objects.filter(
        quotation=quotation, version__lte=quotation.business_version, version__lt=before['scope_before'],
        business_snapshot__draft__owner_id=quotation.cart.owner_id).order_by('-version').values(
            'version', 'business_snapshot__version', 'created_at')[:PAGE_SIZE + 1]
    reviews = QuotationReview.objects.filter(
        quotation=quotation, version__lte=quotation.review_version, version__lt=before['review_before'],
        business_version__lte=quotation.business_version).order_by('-version').values(
            'version', 'business_version', 'decision', 'created_at')[:PAGE_SIZE + 1]
    events = []
    for row in scopes:
        events.append({'kind': 'business_attachment', 'version': row['version'], 'business_scope': row['version'],
                       'business_draft_version': row['business_snapshot__version'],
                       'label': 'Saved business revision attached; fresh review required', 'created_at': row['created_at']})
    for row in reviews:
        decision = row['decision'] if row['decision'] in DECISIONS else 'unavailable'
        events.append({'kind': 'review', 'version': row['version'], 'business_scope': row['business_version'],
                       'business_draft_version': None, 'label': LABELS[decision], 'created_at': row['created_at']})
    # Writes serialize on the quotation: scope N attaches before its reviews;
    # global review versions and scope versions are the authoritative ordering.
    events.sort(key=lambda event: (event['business_scope'], event['kind'] == 'review', event['version']), reverse=True)
    more = len(events) > PAGE_SIZE
    events = events[:PAGE_SIZE]
    next_before = dict(before)
    for event in events:
        name = 'scope_before' if event['kind'] == 'business_attachment' else 'review_before'
        next_before[name] = min(next_before[name], event['version'])
    if not more:
        events.append({'kind': 'capture', 'version': quotation.snapshot.version, 'business_scope': 0,
                       'business_draft_version': None, 'label': 'Quotation requested from captured cart', 'created_at': quotation.created_at})
    return {'events': events, 'older_query': urlencode(next_before) if more else None,
            'status': customer_review_status(quotation), 'page_size': PAGE_SIZE,
            'business_version': quotation.business_version, 'review_version': quotation.review_version}
