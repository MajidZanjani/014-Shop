"""Full synthetic refunds reuse finance operations; support adjustments stay manual."""
import uuid
from django.db import transaction
from shop.catalog import checkout_payment as payment
from shop.payments import operations, attempts, observations, notifications
from shop.payments.models import SyntheticPaymentOperation, SyntheticOperationResult
from . import catalog, checkout, paid_orders
from .errors import ShbError
from .models import PaidOrder, PaidOrderGrant, RefundReview, RefundSupportHandoff

FLAGS = {**operations.FLAGS, 'support_tracking':'manual-outside-shop', 'actual_email_sent':False}


def text(value, maximum):
    if type(value) is not str or not 1 <= len(value.strip()) <= maximum:
        raise ShbError('invalid_request', 400)
    return value.strip()


def reference(review):
    return {'id':str(review.pk), 'sha256':review.sha256, 'order_id':str(review.order_id),
        'order_reference':review.order.payload['order_reference']}


def retained_review(review, accepted, archive):
    order = review.order
    expected = {'order_id':str(order.pk), 'order_reference':order.payload['order_reference'],
        'schema':1, 'kind':'shb-refund-review', 'request_id':str(review.request_id),
        'order_sha256':order.sha256, 'acceptance_id':str(accepted.pk), 'acceptance_sha256':accepted.sha256,
        'attempt_id':str(accepted.attempt_id), 'amount_minor':order.payload['purchase']['total_minor'],
        'currency':order.payload['purchase']['currency']}
    if (review.pk != uuid.uuid5(order.pk, 'shb-refund-review-v1') or order.acceptance_id != accepted.pk
            or review.sha256 != catalog.digest(review.payload)
            or any(review.payload.get(key) != value for key,value in {**expected, **FLAGS}.items())
            or review.payload.get('manual_records_checked') is not True
            or review.payload.get('financial_policy') != operations.POLICY):
        raise ShbError('shb_refund_review_required')
    payment.recover(archive, review.archive_receipt, review.pk, catalog.canonical(review.payload))


def required_reference(accepted, archive):
    review = RefundReview.objects.select_related('order').filter(order__acceptance=accepted).first()
    if review is None: raise ShbError('shb_refund_review_required')
    retained_review(review, accepted, archive)
    return reference(review)


def verify_operation(row, accepted, archive, *, dispatch=False):
    if accepted.checkout.snapshot.get('release') != 'shb-1.1' or row.kind != 'refund': return
    saved = row.payload.get('shb_refund_review')
    # Existing immutable historical intents remain readable/reconcilable. New
    # inserts are also SQL-gated; no unreviewed historical intent can dispatch.
    if saved is None and not dispatch: return
    if saved != required_reference(accepted, archive): raise ShbError('shb_refund_review_required')


def authorized(request, identity, archive):
    from .staff_orders import credential
    credential(request)  # Epoch precedes credential/customer/financial locks.
    grant = PaidOrderGrant.objects.select_for_update().select_related('order__acceptance__checkout').filter(
        user=request.user, order_id=identity).first()
    if grant is None: raise ShbError('not_found', 404)
    accepted, attempt, actor = operations.scope_locked(request, grant.order.acceptance_id, 'refund', archive)
    order = PaidOrder.objects.select_for_update().select_related('capture').get(pk=identity)
    events, _ = observations.history_locked(attempt, archive)
    if not any(event.pk == order.capture_id for event in events): paid_orders.fail()
    paid_orders.retained(order, accepted, order.capture, archive)
    return order, accepted, attempt, actor


def record_review(request, identity, value, archive):
    checkout.guard()
    key = checkout.identity(value['request_id'])
    if value['manual_records_checked'] is not True: raise ShbError('manual_support_record_check_required', 422)
    note = text(value['manual_record_reference'], 200); reason = text(value['reason'], 512)
    with transaction.atomic(durable=True):
        order, accepted, attempt, actor = authorized(request, identity, archive)
        saved = RefundReview.objects.select_related('order').filter(order=order).first()
        if saved:
            retained_review(saved, accepted, archive)
            if (saved.request_id != key or saved.payload['manual_record_reference'] != note
                    or saved.payload['reason'] != reason or saved.payload['actor']['staff_id'] != actor['staff_id']):
                raise ShbError('request_conflict')
            return saved, False
        if attempt.provider_status != 'captured': raise ShbError('captured_original_order_required')
        payload = {'schema':1, 'kind':'shb-refund-review', 'order_id':str(order.pk),
            'request_id':str(key),
            'order_reference':order.payload['order_reference'], 'order_sha256':order.sha256,
            'acceptance_id':str(accepted.pk), 'acceptance_sha256':accepted.sha256, 'attempt_id':str(attempt.pk),
            'amount_minor':attempt.amount_minor, 'currency':attempt.currency,
            'manual_records_checked':True, 'manual_record_reference':note, 'reason':reason,
            'actor':actor, 'recorded_at':attempts.database_now().isoformat(),
            'financial_policy':operations.POLICY.copy(), **FLAGS}
        identity = uuid.uuid5(order.pk, 'shb-refund-review-v1')
        evidence = notifications.evidence(identity, payload, archive)
        operations.staff_locked(request, accepted.pk, 'refund')
        return RefundReview.objects.create(id=identity, order=order, request_id=key, **evidence), True


def retained_handoff(saved, review, result, archive):
    if (saved.pk != uuid.uuid5(review.pk, 'shb-refund-handoff-v1') or saved.review_id != review.pk
            or saved.result_id != result.pk or saved.sha256 != catalog.digest(saved.payload)
            or saved.payload.get('refund_review') != reference(review)
            or saved.payload.get('result_sha256') != result.sha256
            or saved.payload.get('result_id') != str(result.pk)
            or saved.payload.get('request_id') != str(saved.request_id)
            or any(saved.payload.get(key) != value for key,value in FLAGS.items())
            or saved.payload.get('support_team_informed') is not True):
        raise ShbError('shb_refund_handoff_evidence_required')
    operation = result.operation
    notifications.retained(operation, archive)
    operations.retained_result(operation, operations.mutation(operation), result, archive)
    payment.recover(archive, saved.archive_receipt, saved.pk, catalog.canonical(saved.payload))


def record_handoff(request, identity, value, archive):
    checkout.guard(); key = checkout.identity(value['request_id'])
    note = text(value['communication_reference'], 200)
    with transaction.atomic(durable=True):
        order, accepted, attempt, actor = authorized(request, identity, archive)
        review = RefundReview.objects.select_related('order').filter(order=order).first()
        if review is None: raise ShbError('shb_refund_review_required')
        retained_review(review, accepted, archive)
        operation = SyntheticPaymentOperation.objects.filter(acceptance=accepted, kind='refund').first()
        if operation is None: raise ShbError('confirmed_refund_required')
        operation, attempt, delivery, command = operations.locked(request, operation.pk, archive)
        if delivery.state != 'observed' or attempt.provider_status != 'refunded': raise ShbError('confirmed_refund_required')
        result = SyntheticOperationResult.objects.get(operation=operation)
        operations.retained_result(operation, command, result, archive)
        saved = RefundSupportHandoff.objects.filter(review=review).first()
        if saved:
            retained_handoff(saved, review, result, archive)
            if (saved.request_id != key or saved.payload['communication_reference'] != note
                    or saved.payload['actor']['staff_id'] != actor['staff_id']): raise ShbError('request_conflict')
            return saved, False
        payload = {'schema':1, 'kind':'shb-refund-support-handoff', 'refund_review':reference(review),
            'request_id':str(key),
            'result_id':str(result.pk), 'result_sha256':result.sha256,
            'support_team_informed':True, 'communication_reference':note, 'actor':actor,
            'recorded_at':attempts.database_now().isoformat(), **FLAGS}
        identity = uuid.uuid5(review.pk, 'shb-refund-handoff-v1')
        evidence = notifications.evidence(identity, payload, archive)
        operations.staff_locked(request, accepted.pk, 'refund')
        return RefundSupportHandoff.objects.create(id=identity, review=review, result=result,
            request_id=key, **evidence), True
