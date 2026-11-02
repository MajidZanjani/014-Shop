"""One minimal form for both variants; no licence/board/host questionnaire."""
import re
from django import forms
from .catalog import CATALOG, MAX_QUANTITY


class WholeBundles(forms.CharField):
    def to_python(self,value):
        value=super().to_python(value)
        if not re.fullmatch(r'[1-9][0-9]{0,9}',value or ''):
            raise forms.ValidationError('Enter a positive whole number of bundles.')
        quantity=int(value)
        if quantity>MAX_QUANTITY:raise forms.ValidationError('The quantity is too large.')
        return quantity


class Phone(forms.CharField):
    def validate(self,value):
        super().validate(value)
        if value and (not re.fullmatch(r'[+0-9(). /-]{5,40}',value) or len(re.sub('[^0-9]','',value))<5):
            raise forms.ValidationError('Enter a phone number, including the country code where needed.')


class ShopForm(forms.Form):
    variant=forms.ChoiceField(label='Bundle',choices=[(v['id'],v['label']) for v in CATALOG['variants']])
    quantity=WholeBundles(label='Bundle quantity',initial='1',widget=forms.NumberInput(attrs={'min':1,'step':1,'inputmode':'numeric'}))
    company_name=forms.CharField(label='Company Name',max_length=200)
    billing_address=forms.CharField(label='Address',max_length=500,widget=forms.Textarea(attrs={'rows':2,'autocomplete':'street-address'}))
    country=forms.RegexField(label='Billing country (two-letter code)',regex=r'^[A-Za-z]{2}$',max_length=2)
    city=forms.CharField(label='City',max_length=100,required=False)
    region=forms.CharField(label='Region / state (if applicable)',max_length=100,required=False)
    postal_code=forms.CharField(label='Postal code (if applicable)',max_length=32,required=False)
    company_phone=Phone(label='Company Phone',max_length=40)
    contact_name=forms.CharField(label='Contact Person (Full Name)',max_length=160)
    same_phone=forms.BooleanField(label='Same as company phone',required=False)
    contact_phone=Phone(label='Contact Phone Number',max_length=40,required=False)
    contact_email=forms.EmailField(label='Contact Email',max_length=254)
    tax_identifier=forms.CharField(label='VAT / tax identifier (where applicable)',max_length=64,required=False)
    tax_not_applicable=forms.BooleanField(label='Tax identifier not applicable',required=False)
    discount_code=forms.RegexField(label='Discount code (optional)',regex=r'^[A-Za-z0-9-]{1,48}$',max_length=48,required=False,widget=forms.TextInput(attrs={'autocomplete':'off','autocapitalize':'characters','spellcheck':'false'}))
    assistance=forms.CharField(label='What assistance do you need? (ASIC)',max_length=2000,required=False,widget=forms.Textarea(attrs={'rows':4}))
    project_reference=forms.CharField(label='SLL IP/product or support/project reference (ASIC, if not already known)',max_length=160,required=False)
    design_context=forms.CharField(label='Design stage, technology/process and tools (optional; Not yet known is allowed)',max_length=500,required=False)
    timing=forms.CharField(label='Desired timing (optional; No fixed deadline is allowed)',max_length=160,required=False)
    privacy_acknowledged=forms.BooleanField(label='I acknowledge the applicable Privacy Policy.',required=False)
    accept_terms=forms.BooleanField(label='I accept the applicable purchase, support and refund terms.',required=False)

    def __init__(self,*args,stage='review',known_project=False,tax_rules=None,**kwargs):
        self.stage=stage;self.known_project=known_project;self.tax_rules=tax_rules or {}
        super().__init__(*args,**kwargs)
        self.fields['privacy_acknowledged'].required=stage in ('submit','checkout')
        self.fields['accept_terms'].required=stage=='checkout'

    def clean(self):
        data=super().clean()
        if self.is_bound:
            allowed=set(self.fields)|{'csrfmiddlewaretoken','action','request_id','review_digest'}
            if set(self.data)-allowed:self.add_error(None,'The submitted fields are not supported. Review the form again.')
            if hasattr(self.data,'getlist') and any(len(self.data.getlist(k))!=1 for k in self.data):
                self.add_error(None,'Repeated form fields are not supported.')
        if data.get('same_phone'):data['contact_phone']=data.get('company_phone','')
        elif not data.get('contact_phone'):self.add_error('contact_phone','Enter a contact phone or choose Same as company phone.')
        if data.get('country'):data['country']=data['country'].upper()
        rules=self.tax_rules.get(data.get('country'),{})
        for field in rules.get('required_fields',[]):
            if field not in ('city','region','postal_code','tax_identifier'):raise ValueError('invalid_tax_rule')
            if not data.get(field):self.add_error(field,'This field is required by the applicable billing rules.')
        if data.get('tax_identifier') and data.get('tax_not_applicable'):
            self.add_error('tax_identifier','Choose either an applicable identifier or Not applicable.')
        if data.get('variant')=='shb-asic-25h':
            if not data.get('assistance'):self.add_error('assistance','Briefly describe the assistance and objective.')
            if not self.known_project and not data.get('project_reference'):
                self.add_error('project_reference','Identify the SLL IP/product or existing support/project reference.')
        else:
            # Engineering triage belongs only to ASIC; it is never a prerequisite
            # for buying an ordinary eligible FPGA top-up.
            for field in ('assistance','project_reference','design_context','timing'):data[field]=''
        if data.get('discount_code'):data['discount_code']=data['discount_code'].upper()
        return data


class OfferForm(ShopForm):
    """Fresh billing/contact input; quantity and engineering scope come from the offer."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ('variant', 'quantity', 'discount_code', 'assistance', 'project_reference', 'design_context', 'timing'):
            self.fields.pop(name)
