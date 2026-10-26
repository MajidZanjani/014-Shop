"""Explicit synthetic standard offers. Never approved live commercial policy."""
from copy import deepcopy
from dataclasses import dataclass
from .rules import CATALOG,evaluate

FIXTURE_KITS=({'id':'synthetic-kit-rev-a','label':'Synthetic kit · standard revision A'},)

@dataclass(frozen=True)
class FixtureOffer:
    id: str
    kind: str
    support_required: bool | None
    minimum_packages: int | None
    licence_minor: int | None
    support_minor: int | None
    rights: str | None='synthetic-rd-rights'
    annual_start: str | None='synthetic-funded-start'
    delivery: str | None='Synthetic approved initial RTL/key/docs; reference design as described'
    revision: str='synthetic-policy-v1'
    vendor: str='altera'
    families: tuple=('altera-max-10',)
    term: str='rd-annual'
    kit_id: str | None=None
    later_reference_design: bool=True

FIXTURE_OFFERS=(
    FixtureOffer('synthetic-ready-kit','ready-kit',False,0,12345,2345,kit_id='synthetic-kit-rev-a',later_reference_design=False),
    FixtureOffer('synthetic-development','development',True,2,12345,2345),
)


def quote(configuration,offer_id,*,offers=FIXTURE_OFFERS):
    """No custom-board review rule; only missing applicable commercial facts hold."""
    errors=[];offer=next((o for o in offers if o.id==offer_id),None)
    result=evaluate(configuration,kit_catalog=FIXTURE_KITS)
    if not result['valid']:errors.append('invalid_licence_or_platform')
    if offer is None:errors.append('offer_unavailable')
    platform=configuration.get('platform') if isinstance(configuration,dict) else None
    if platform is None:errors.append('platform_required_for_purchase')
    status='invalid' if errors else 'synthetic_purchasable'
    if not errors:
        if (configuration['vendor']!=offer.vendor or configuration['term']!=offer.term
            or any(f not in offer.families for f in configuration['families'])):
            errors.append('licence_scope_not_covered');status='awaiting_review'
        if offer.kind=='ready-kit' and (platform['choice']!='listed-kit' or platform['kit_id']!=offer.kit_id):
            errors.append('ready_design_not_applicable');status='unavailable'
        if (not offer.rights or not offer.annual_start or not offer.delivery
            or offer.support_required is None or offer.minimum_packages is None or offer.licence_minor is None
            or (configuration['support_packages'] and offer.support_minor is None)
            or offer.kind not in ('ready-kit','development')
            or type(offer.support_required) is not bool or type(offer.licence_minor) is not int or offer.licence_minor<1
            or (offer.support_minor is not None and (type(offer.support_minor) is not int or offer.support_minor<0))):
            errors.append('pending_commercial_policy');status='awaiting_review'
        elif (type(offer.minimum_packages) is not int or offer.minimum_packages<0
              or (offer.support_required and offer.minimum_packages<1)
              or (not offer.support_required and offer.minimum_packages!=0)):
            errors.append('invalid_support_policy');status='awaiting_review'
        elif configuration['support_packages']<offer.minimum_packages:
            errors.append('required_support_minimum');status='invalid'
    total=None;snapshot=None
    if not errors:
        total=offer.licence_minor+configuration['support_packages']*(offer.support_minor or 0)
        if type(total) is not int or not 1<=total<=9223372036854775807:
            errors.append('invalid_total');status='awaiting_review';total=None
        else:
            snapshot={'schema':1,'evidence_class':'local-synthetic','configuration':deepcopy(configuration),
                'offer_id':offer.id,'offer_revision':offer.revision,'support_policy':'required' if offer.support_required else 'optional',
                'minimum_packages':offer.minimum_packages,'support_packages':configuration['support_packages'],
                'rights':offer.rights,'annual_start':offer.annual_start,'delivery':offer.delivery,
                'later_reference_design':offer.later_reference_design,'currency':'EUR','total_minor':total,
                'financial_confirmation':False,'effects_authorized':False}
    return {'status':status,'errors':errors,'total_minor':total,'snapshot':snapshot,
        'evidence_class':'local-synthetic','financial_confirmation':False,'effects_authorized':False}
