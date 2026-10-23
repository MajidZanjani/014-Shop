"""Closed customer projection. Never serialize staff review records."""
from django.db.models import OuterRef, Subquery
from .models import QuotationReview

LABELS={
    'awaiting_review':'Awaiting review',
    'needs_information':'Scope clarification needed',
    'ready_for_commercial_review':'Ready for commercial review — no offer approved',
    'declined':'Request declined',
    'unavailable':'Review status unavailable',
}


def with_review_status(rows):
    # Correlate exact committed counter and event within one owner-list query.
    current=QuotationReview.objects.filter(quotation_id=OuterRef('pk'),version=OuterRef('review_version'))
    return rows.annotate(customer_review_decision=Subquery(current.values('decision')[:1]),
                         customer_review_time=Subquery(current.values('created_at')[:1]),
                         customer_review_scope=Subquery(current.values('business_version')[:1]))


def customer_review_status(row):
    if row.review_version==0:
        return {'code':'awaiting_review','label':LABELS['awaiting_review'],'version':0,'updated_at':None}
    if hasattr(row,'customer_review_decision'):
        decision=row.customer_review_decision;updated=row.customer_review_time
        scope=getattr(row,'customer_review_scope',0)
    else:
        record=QuotationReview.objects.filter(quotation=row,version=row.review_version).values('decision','created_at','business_version').first()
        decision=record['decision'] if record else None
        updated=record['created_at'] if record else None
        scope=record['business_version'] if record else None
    if scope is not None and scope!=getattr(row,'business_version',0):
        return {'code':'awaiting_review','label':LABELS['awaiting_review'],'version':0,'updated_at':None}
    if decision not in {'needs_information','ready_for_commercial_review','declined'} or updated is None:
        return {'code':'unavailable','label':LABELS['unavailable'],'version':None,'updated_at':None}
    return {'code':decision,'label':LABELS[decision],'version':row.review_version,'updated_at':updated.isoformat()}
