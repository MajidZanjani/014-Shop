"""Private SHB form/review and persisted synthetic ASIC request; no live purchase."""
from pathlib import Path
import uuid
from django.conf import settings
from django.http import HttpResponse,JsonResponse,HttpResponseRedirect
from django.template.response import TemplateResponse
from django.views.decorators.http import require_GET,require_http_methods
from . import catalog,invitations,services,discounts
from .forms import ShopForm
from .middleware import denied
from .private_release import read_asset,ENTRY


def page(request,**context):
    response=TemplateResponse(request,'shb/shop.html',context,status=context.pop('status',200))
    response['Content-Security-Policy']="default-src 'none'; style-src 'self'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'"
    response['Cache-Control']='no-store';response['Referrer-Policy']='no-referrer'
    return response


@require_GET
def invite(request,token):
    if invitations.exchange(request,token) is None:return denied()
    return HttpResponseRedirect('/shop/')


@require_GET
def catalog_json(request):
    # No invitation secrets, company identity, saved details or price authority.
    response=JsonResponse(catalog.CATALOG)
    response['Cache-Control']='no-store'
    return response


@require_GET
def stylesheet(request):
    return HttpResponse(Path(__file__).with_name('shop.css').read_text(),content_type='text/css; charset=utf-8')


@require_GET
def static_asset(request,name=ENTRY):
    root=getattr(settings,'SHB_PRIVATE_RELEASE_ROOT',None)
    expected=getattr(settings,'SHB_PRIVATE_RELEASE_SHA256',None)
    if not root or not expected:return denied(404)
    try:raw,mime,policy=read_asset(root,expected,name)
    except (ValueError,OSError,KeyError,TypeError):return denied(404)
    response=HttpResponse(raw,content_type=mime)
    response['X-Content-Type-Options']='nosniff'
    if policy:response['Content-Security-Policy']=policy
    return response


@require_http_methods(['GET','POST'])
def shop(request):
    invitation=request.shb_invitation
    fixture=getattr(settings,'SHB_SYNTHETIC_FIXTURE',False) and settings.SHOP_ENV in ('local','synthetic')
    if request.method=='GET':
        if request.path=='/shop/' and getattr(settings,'SHB_PRIVATE_RELEASE_ROOT',None):return static_asset(request)
        variant=request.GET.get('variant','shb-fpga-10h');quantity=request.GET.get('quantity','1')
        if (set(request.GET)-{'variant','quantity'} or variant not in ('shb-fpga-10h','shb-asic-25h')
                or not 1<=len(quantity)<=10 or not quantity.isascii() or not quantity.isdecimal() or not 1<=int(quantity)<=catalog.MAX_QUANTITY):return denied(400)
        return page(request,form=ShopForm(initial={'variant':variant,'quantity':quantity}),request_id=str(uuid.uuid4()),fixture=fixture,is_asic=variant=='shb-asic-25h',asic_fields=('assistance','project_reference','design_context','timing'))
    if request.content_type not in ('application/x-www-form-urlencoded','multipart/form-data'):
        return page(request,form=ShopForm(),error='Use the protected form.',status=415)
    if request.FILES:return page(request,form=ShopForm(),error='Files are not accepted by this form.',status=422)
    action=request.POST.get('action','review')
    posted=request.POST.copy()
    if action=='remove_discount' and len(posted.getlist('discount_code'))<=1:posted['discount_code']=''
    form=ShopForm(posted,stage='submit' if action=='submit' else 'review',known_project=bool(invitation.project_reference))
    context={'form':form,'request_id':request.POST.get('request_id',''),'fixture':fixture,
        'is_asic':request.POST.get('variant')=='shb-asic-25h','asic_fields':('assistance','project_reference','design_context','timing')}
    if not form.is_valid():return page(request,**context,status=422)
    data=form.cleaned_data
    if data['company_name'].strip()!=invitation.company_name:
        return page(request,**context,error='Contact SLL to clarify a different purchasing company.',status=409)
    if data['variant']=='shb-fpga-10h' and not invitation.fpga_eligible or data['variant']=='shb-asic-25h' and not invitation.asic_allowed:
        return page(request,**context,error='Contact SLL to clarify eligibility for this support.',status=422)
    try:
        if action=='submit':
            if not fixture:raise services.ShbError('Live request intake awaits its approved privacy and operational configuration.',503)
            row=services.submit_asic(request,data,request.POST.get('request_id'))
            from .models import DiscountReservation
            hold=DiscountReservation.objects.filter(request=row).first()
            message=('The unused discount reservation was released.' if hold and hold.state=='released'
                else 'Discount reserved for this request; review may continue after its claim deadline.' if hold else None)
            state_label={'submitted':'Submitted for review','under_review':'Under review',
                'needs_information':'More information required','declined':'Declined',
                'withdrawn':'Withdrawn','approved':'Approved for offer preparation',
                'offer_issued':'Offer issued','paid':'Paid'}.get(row.state,'Contact SLL')
            return page(request,**context,submitted=row,purchase=row.payload['purchase'],
                request_status=state_label,discount_message=message)
        if action not in ('review','apply_discount','remove_discount'):
            raise services.ShbError('Checkout awaits the integrated SHB order/payment batch.',503)
        if action=='apply_discount' and not data['discount_code']:
            raise services.ShbError('Enter a discount code to apply.',422)
        value=discounts.preview(request,data) if data['discount_code'] else catalog.quote(
            data['variant'],data['quantity'],offer=catalog.synthetic_offer() if fixture else None)
        message='Discount applied to this preview. A use is reserved only on submission or checkout.' if data['discount_code'] else 'Discount removed.' if action=='remove_discount' else None
        return page(request,**context,purchase=value,discount_message=message)
    except services.ShbError as error:return page(request,**context,error=error.code,status=error.status)
    except ValueError:return page(request,**context,error='The requested quantity or amount is outside the applicable limits.',status=422)
