"""Internal synthetic numbering journal. No legal document publication or live authority."""
import uuid
from django.db import connection, transaction
from shop.adapters.evidence_archive import manifest
from shop.payments.synthetic_bank import guard
from . import checkout, checkout_payment as payment
from .models import SyntheticDocumentReservation as Reservation, SyntheticDocumentIssue as Issue


def fail():
    raise checkout.CheckoutError('synthetic_document_history_hold',409)


def verify(row, archive):
    value=row.payload
    if row.sha256 != checkout.digest(value) or value.get('identity') != str(row.pk):fail()
    if value.get('effects_authorized') is not False or value.get('evidence_class') != 'local-synthetic':fail()
    payment.recover(archive,row.archive_receipt,row.pk,checkout.canonical(value))
    return value


def lock(kind):
    if connection.vendor != 'postgresql' or kind not in ('invoice','credit'):fail()
    # Stable, disjoint transaction locks serialize even an empty journal.
    with connection.cursor() as cursor:
        cursor.execute('SELECT pg_advisory_xact_lock(%s, %s)',[104004,1 if kind=='invoice' else 2])


def retained(kind, archive):
    rows=list(Reservation.objects.filter(kind=kind).order_by('number')[:10001])
    # Bounded local rehearsal; reaching the cap holds rather than skipping verification.
    if len(rows)>10000:fail()
    previous=None
    for number,row in enumerate(rows,1):
        value=verify(row,archive)
        if (row.number!=number or value.get('number')!=number or value.get('kind')!=kind
                or value.get('request_id')!=str(row.request_id) or value.get('subject')!=str(row.subject)
                or value.get('previous_sha256')!=previous):fail()
        issued=Issue.objects.filter(reservation=row).first()
        if issued:
            issued_value=verify(issued,archive)
            if issued_value.get('reservation_sha256')!=row.sha256:fail()
        previous=row.sha256
    return rows,previous


def persist(model, identity, value, archive, **fields):
    body=checkout.canonical(value)
    receipt=manifest(archive.publish(identity,body))
    payment.recover(archive,receipt,identity,body)
    return model.objects.create(id=identity,payload=value,sha256=checkout.digest(value),archive_receipt=receipt,**fields)


def reserve(kind, request_id, subject, archive):
    guard()
    if type(request_id) is not uuid.UUID or type(subject) is not uuid.UUID:fail()
    with transaction.atomic(durable=True):
        lock(kind)
        rows,previous=retained(kind,archive)
        prior=Reservation.objects.filter(request_id=request_id).first()
        if prior:
            if prior.kind!=kind or prior.subject!=subject:fail()
            return prior
        identity=uuid.uuid4();number=len(rows)+1
        value={'identity':str(identity),'kind':kind,'number':number,'request_id':str(request_id),
               'subject':str(subject),'previous_sha256':previous,'evidence_class':'local-synthetic',
               'effects_authorized':False,'legal_numbering_approved':False}
        return persist(Reservation,identity,value,archive,kind=kind,number=number,request_id=request_id,subject=subject)


def issue(reservation_id, archive):
    """Record a simulated issue separately; reservation alone never proves issue."""
    guard()
    if type(reservation_id) is not uuid.UUID:fail()
    with transaction.atomic(durable=True):
        candidate=Reservation.objects.filter(pk=reservation_id).first()
        if candidate is None:fail()
        lock(candidate.kind)
        retained(candidate.kind,archive)
        prior=Issue.objects.filter(reservation=candidate).first()
        if prior:return prior
        identity=uuid.uuid4()
        value={'identity':str(identity),'reservation_sha256':candidate.sha256,
               'evidence_class':'local-synthetic','effects_authorized':False,'actual_document_issued':False}
        return persist(Issue,identity,value,archive,reservation=candidate)
