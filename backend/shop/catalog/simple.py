"""Local no-JavaScript configuration preview; never places an order."""
from django import forms
from django.conf import settings
from django.http import HttpResponse
from django.middleware.csrf import get_token
from django.utils.html import format_html, format_html_join
from django.views.decorators.http import require_http_methods
from .rules import CATALOG, evaluate

class ConfigurationForm(forms.Form):
    vendor=forms.ChoiceField(choices=[('', 'Choose a vendor')]+[(v['id'],v['label']) for v in CATALOG['vendors']],error_messages={'invalid_choice':'Choose a listed vendor.'})
    families=forms.MultipleChoiceField(choices=[(v['label'],[(f['id'],f['label']) for f in v['families']]) for v in CATALOG['vendors']],widget=forms.CheckboxSelectMultiple,error_messages={'invalid_choice':'Choose listed families.'})
    term=forms.ChoiceField(choices=[('', 'Choose a term')]+[(t['id'],t['label']) for t in CATALOG['terms']],error_messages={'invalid_choice':'Choose a listed term.'})
    production_band=forms.ChoiceField(required=False,choices=[('', 'Not applicable')]+[(b['id'],b['label']) for b in CATALOG['production_bands']],label='Production band (RDP only)',error_messages={'invalid_choice':'Choose a listed band.'})
    production_units=forms.IntegerField(required=False,min_value=1,max_value=1000000,label='Expected units (optional, RDP only)')
    fixed_nodes=forms.IntegerField(min_value=0,max_value=1000000,initial=0,label='Fixed nodes (Altera only; zero disables)')
    floating_nodes=forms.IntegerField(min_value=0,max_value=1000000,initial=0,label='Floating seats (Altera only; zero disables)')
    support_packages=forms.IntegerField(min_value=0,max_value=1000000,initial=0,label='10-hour support packages (zero means none)')

@require_http_methods(['GET','POST'])
def simple_purchase(request):
    if settings.SHOP_ENV not in ('local','synthetic'): return HttpResponse('Unavailable',status=404)
    result=None;messages=[]
    form=ConfigurationForm()
    if request.method=='POST':
        bound=ConfigurationForm(request.POST)
        valid=bound.is_valid()
        if set(request.POST)-set(bound.fields)-{'csrfmiddlewaretoken'}:
            messages.append('Unexpected fields are not accepted.');valid=False
        if valid:
            data=bound.cleaned_data
            value={'product_id':CATALOG['product_id'],'profile_id':CATALOG['profile_id'],'quantity':1,**data}
            value['production_band']=value['production_band'] or None
            result=evaluate(value)
            messages=[e['field']+': '+e['code'] for e in result['errors']]
        else:
            messages += [field+': check this field.' for field in bound.errors]
        # Only cleaned data is displayed. Invalid raw inputs are never reflected.
        form=ConfigurationForm(initial=bound.cleaned_data)
    outcome='Complete your configuration.'
    if result and result['valid']:
        outcome='Quotation required for higher volume.' if result['status']=='requires_quote' else 'Configuration ready for review.'
    errors=format_html_join('', '<li>{}</li>',((m,) for m in messages))
    response=HttpResponse(format_html('''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><link rel="canonical" href="https://shop.xspi.pro/purchase/simple/"><title>SLL xSPI-MC — simple configuration</title></head><body><main><h1>Configure SLL xSPI-MC</h1><p><a href="/purchase/access/">Customer access without JavaScript</a></p><p>Local preview. Exactly one vendor and one or more of its families per licence. RDP is Altera-only. Access counts are Altera-only; enable one or both modes.</p><form method="post"><input type="hidden" name="csrfmiddlewaretoken" value="{}">{}<button>Review configuration</button></form><h2>{}</h2><ul>{}</ul><p>Price: pending approval (EUR draft). Higher volume requires a reviewed quotation. Rights, access, coverage, production counting and final terms await approval.</p><button disabled>Purchase unavailable</button><p>No host identifiers are collected. Nothing is saved or submitted as an order. Support hours do not expire and never renew IP rights.</p></main></body></html>''',get_token(request),form.as_p(),outcome,errors))
    response['Cache-Control']='no-store'
    return response
