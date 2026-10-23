"""Immutable business binding helpers; customer summaries contain revision metadata only."""
from django.db.models import F
from .models import QuotationBusinessScope
from . import business_rules as rules

def scope_for_version(quotation,version):
    if not version:return None
    return QuotationBusinessScope.objects.select_related('business_snapshot__draft').filter(quotation=quotation,version=version,business_snapshot__draft__owner_id=F('quotation__cart__owner_id')).first()

def current_scope(quotation):
    return scope_for_version(quotation,quotation.business_version)

def valid_business(snapshot,owner_id):
    clean,errors=rules.validate_details(snapshot.details)
    return (not errors and snapshot.draft.owner_id==owner_id and snapshot.schema_version==rules.SCHEMA_VERSION
            and snapshot.source_sha256==rules.SOURCE_SHA256 and snapshot.details==rules.resolve_details(clean)
            and snapshot.evaluation==rules.evaluate_details(snapshot.details))

def scope_metadata(quotation):
    scope=current_scope(quotation)
    if scope is None:
        return None if not quotation.business_version else {'version':quotation.business_version,'business_draft_version':None,'state':'unavailable'}
    return {'version':scope.version,'business_draft_version':scope.business_snapshot.version,'state':'partial_business_details','country_tax_choices':'pending'}
