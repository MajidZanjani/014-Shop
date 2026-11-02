"""Read-only SHB checks within the existing disposable recovery quarantine.

This checks facts present in the fixture database against retained local bytes.
It cannot establish completeness after a backup, reconstruct missing events,
authorize a bank retry, or qualify actual reopening.
"""
from contextlib import nullcontext
from pathlib import Path
import uuid

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection, transaction

from shop.access.effects import _guard, drain_state
from shop.access.models import AccessEpoch
from shop.adapters.evidence_archive import PreparedArchive
from shop.catalog import checkout as shared, checkout_payment as payment
from shop.catalog.models import SyntheticCheckoutAcceptance
from shop.payments import attempts, observations, operations
from shop.payments.models import SyntheticPaymentOperation,SyntheticOperationDispatch,SyntheticOperationResult
from . import catalog, closures, invitations, lifecycle, offers, paid_orders, purchase_mail, revisions, transaction_mail,refunds
from .errors import ShbError
from .models import (CheckoutClosure, DiscountReservation, Invitation, PaidOrder,
    PurchaseNoticeCapture, PurchaseNoticeDelivery, RequestClosure, RequestReplacement,
    SupportCheckout, SupportOffer, SupportRequest, SupportRequestReview,
    TransactionNotice, TransactionNoticeCapture, TransactionNoticeDelivery,RefundReview,RefundSupportHandoff,InvitationRevocation,DiscountIssue)


def require(condition):
    if not condition:
        raise ShbError('shb_recovery_evidence_required', 503)


def _delivery(row, capture, verify):
    require(row is not None)
    require(row.state != 'captured' or capture is not None)
    if capture is not None:
        verify(capture)
    # Pending/claimed/held work keeps its original lease, attempts and identity.
    # A fake capture does not prove actual mail delivery or permit a resend.


def _records(archive):
    expected_notices = set()

    def notice(event, source):
        key = uuid.uuid5(uuid.NAMESPACE_URL, 'sll-shb-transaction:' + event + ':' + str(source.pk))
        saved = TransactionNotice.objects.filter(pk=key).first()
        expected = transaction_mail.value(event, source)
        require(saved is not None and saved.event == event and saved.source_id == str(source.pk)
            and saved.payload == expected and saved.sha256 == catalog.digest(expected))
        expected_notices.add(key)
        capture = TransactionNoticeCapture.objects.filter(notice=saved).first()
        _delivery(TransactionNoticeDelivery.objects.filter(notice=saved).first(), capture,
            lambda captured: transaction_mail.retained(captured, saved, archive))

    for invite in Invitation.objects.all().iterator():
        require(invite.expires_at == invitations.six_month_expiry(invite.created_at))

    from . import invitation_admin
    for event in InvitationRevocation.objects.select_related('invitation').iterator():
        invitation_admin.retained(event,archive)

    from . import invitation_issuance
    from .models import InvitationIssue
    for event in InvitationIssue.objects.select_related('scope','replaces','invitation').iterator():
        invitation_issuance.retained(event,archive)

    from . import discount_admin
    from .models import DiscountRevocation
    for event in DiscountRevocation.objects.select_related('discount').iterator():
        discount_admin.retained(event,archive)

    from . import discount_issuance
    from .models import DiscountIssue
    for event in DiscountIssue.objects.select_related('scope','discount').iterator():
        discount_issuance.retained(event,archive)

    for row in SupportRequest.objects.select_related('invitation', 'quotation__cart', 'quotation__snapshot').iterator():
        require(row.sha256 == catalog.digest(row.payload)
            and row.payload['invitation_id'] == str(row.invitation_id)
            and row.payload['customer_id'] == row.invitation.customer_id == row.quotation.cart.owner_id
            and row.quotation.snapshot.lines == [row.payload['purchase']])
        require(bool(row.payload['purchase'].get('discount_policy'))
            == DiscountReservation.objects.filter(request=row).exists())
        origin = RequestReplacement.objects.select_related('previous__invitation', 'closure', 'invitation').filter(request=row).first()
        require(bool(origin) == ('replaces_request_id' in row.payload))
        if origin:
            previous = origin.previous
            require(origin.pk == uuid.uuid5(row.pk, 'shb-request-replacement-v1')
                and origin.invitation_id == row.invitation_id
                and origin.closure.request_id == previous.pk and origin.closure.applied_at is not None
                and origin.closure.payload['action'] == 'withdraw' and previous.state == 'withdrawn'
                and row.revision == previous.revision + 1 == row.payload['request_revision']
                and row.payload['replaces_request_id'] == str(previous.pk)
                and row.payload['replaces_closure_id'] == str(origin.closure_id)
                and row.payload['replaces_request_sha256'] == previous.sha256
                and previous.invitation.customer_id == row.invitation.customer_id
                and previous.invitation.company_name == row.invitation.company_name
                and revisions.project(previous) == revisions.project(row)
                and not DiscountReservation.objects.filter(request=previous, state__in=('reserved', 'consumed')).exists())
        notice('request-received', row)

    for review in SupportRequestReview.objects.select_related('review', 'request__invitation').iterator():
        event = {'needs_information':'request-question', 'declined':'request-declined'}.get(review.review.decision)
        if event:
            notice(event, review)

    for offer in SupportOffer.objects.select_related('request__invitation').iterator():
        offers.verify(offer)
        if offer.published_at is not None:
            offers.recover(offer, archive)
            notice('offer-issued', offer)

    for scope in SupportCheckout.objects.select_related('checkout', 'invitation', 'offer').iterator():
        saved = scope.checkout
        require(saved.sha256 == shared.digest(saved.snapshot)
            and saved.snapshot['customer_id'] == saved.owner_id == scope.invitation.customer_id
            and saved.snapshot['invitation_id'] == str(scope.invitation_id))
        if scope.offer_id:
            require(saved.snapshot['asic_offer'] == offers.reference(scope.offer)
                and saved.snapshot['purchase'] == scope.offer.payload['purchase'])
        else:
            require(bool(saved.snapshot['purchase'].get('discount_policy'))
                == DiscountReservation.objects.filter(checkout=saved).exists())
        accepted = SyntheticCheckoutAcceptance.objects.select_related('checkout', 'attempt').filter(checkout=saved).first()
        if accepted and accepted.simulated_accepted_at is not None:
            payment.retained(accepted, archive)
            if accepted.attempt_id:
                attempt = accepted.attempt
                require(attempts.request_for(attempt) == payment.request_for(accepted))
                if attempt.archive_receipt or attempt.state in ('uncertain', 'observed'):
                    attempts.retained(attempt, archive)
                observations.history_locked(attempt, archive)

    for close in CheckoutClosure.objects.select_related('acceptance__checkout', 'acceptance__attempt').iterator():
        closures.verify(close, close.acceptance)
        require(close.acceptance.attempt_id is None or close.acceptance.attempt.state in ('prepared', 'cancelled', 'expired'))
        if close.applied_at is not None:
            payment.recover(archive, close.archive_receipt, close.pk, catalog.canonical(close.payload))
            require(close.acceptance.attempt_id is None or close.acceptance.attempt.state in ('cancelled', 'expired'))
            notice('checkout-closed', close)

    for close in RequestClosure.objects.select_related('request__invitation', 'offer').iterator():
        lifecycle.verify(close)
        if close.applied_at is not None:
            payment.recover(archive, close.archive_receipt, close.pk, catalog.canonical(close.payload))
            require(close.offer_id is None or close.offer.state in ('closed', 'abandoned'))
            notice('request-closed', close)
        else:
            # Never finish an intent, free its concession or renew its clocks here.
            hold = DiscountReservation.objects.filter(request=close.request, state='reserved').first()
            require(close.request.state == close.payload['prior_state']
                and close.payload['reservation_id'] == (str(hold.pk) if hold else '')
                and close.payload['reservation_sha256'] == (hold.sha256 if hold else ''))

    for order in PaidOrder.objects.select_related('acceptance__checkout', 'acceptance__attempt', 'capture').iterator():
        row = order.acceptance
        require(row.simulated_accepted_at is not None and row.attempt_id == order.capture.attempt_id)
        events, _ = observations.history_locked(row.attempt, archive)
        captures = [event for event in events if event.payload['observation']
            and event.payload['observation']['status'] == 'captured']
        require(captures and captures[0].pk == order.capture_id)
        paid_orders.retained(order, row, order.capture, archive)
        captured = PurchaseNoticeCapture.objects.filter(order=order).first()
        if captured:
            require(captured.pk == uuid.uuid5(order.pk, 'shb-notice-capture-v1'))
        _delivery(PurchaseNoticeDelivery.objects.filter(order=order).first(), captured,
            lambda captured: purchase_mail.retained(captured, order, archive))
        notice('purchase-confirmed', order)

    for hold in DiscountReservation.objects.select_related('discount', 'request__invitation', 'checkout',
            'release_lifecycle', 'release_closure', 'release_review__review', 'consumed_order__acceptance').iterator():
        purchase = hold.request.payload['purchase'] if hold.request_id else hold.checkout.snapshot['purchase']
        expected = purchase.get('discount_policy')
        customer = hold.request.invitation.customer_id if hold.request_id else hold.checkout.owner_id
        require(hold.snapshot == expected and hold.sha256 == catalog.digest(expected)
            and expected['discount_id'] == str(hold.discount_id)
            and expected['customer_id'] == hold.discount.customer_id == customer
            and expected['variant_id'] == purchase['variant_id']
            and expected['percentage_bps'] == hold.discount.percentage_bps
            and expected['claim_expires_at'] == hold.discount.expires_at.isoformat())
        if hold.state == 'released':
            if hold.release_lifecycle_id:
                close = hold.release_lifecycle
                require(close.applied_at is not None and close.request_id == hold.request_id
                    and close.payload['release_discount'] is True
                    and close.payload['reservation_id'] == str(hold.pk)
                    and close.payload['reservation_sha256'] == hold.sha256)
            elif hold.release_closure_id:
                close = hold.release_closure
                scope = SupportCheckout.objects.get(checkout_id=close.acceptance.checkout_id)
                require(close.applied_at is not None and (hold.checkout_id == scope.pk
                    or scope.offer_id and scope.offer.request_id == hold.request_id))
            else:
                require(hold.release_review_id and hold.release_review.request_id == hold.request_id
                    and hold.release_review.review.decision == 'declined')
        elif hold.state == 'consumed':
            order = hold.consumed_order
            require(order is not None and paid_orders.reservation_for(order.acceptance).pk == hold.pk)

    require(set(TransactionNotice.objects.values_list('pk', flat=True)) == expected_notices)
    for review in RefundReview.objects.select_related('order__acceptance__checkout').iterator():
        refunds.retained_review(review,review.order.acceptance,archive)
    financial = SyntheticPaymentOperation.objects.filter(acceptance__checkout__supportcheckout__isnull=False)
    for row in financial.select_related('acceptance__checkout','acceptance__attempt').iterator():
        accepted = row.acceptance
        command = operations.retained(row,accepted,accepted.attempt,archive)
        delivery = SyntheticOperationDispatch.objects.filter(operation=row).first()
        result = SyntheticOperationResult.objects.filter(operation=row).first()
        require(delivery is not None and (delivery.state!='observed' or result is not None))
        if result:operations.retained_result(row,command,result,archive)
    for handoff in RefundSupportHandoff.objects.select_related('review__order','result__operation').iterator():
        refunds.retained_handoff(handoff,handoff.review,handoff.result,archive)
    return {
        'requests':SupportRequest.objects.count(), 'request_replacements':RequestReplacement.objects.count(),
        'paid_orders':PaidOrder.objects.count(), 'pending_request_closures':lifecycle.pending().count(),
        'pending_checkout_closures':closures.pending().count(), 'pending_paid_orders':paid_orders.pending().count(),
        'transaction_notices':len(expected_notices), 'transaction_captures':TransactionNoticeCapture.objects.count(),
        'held_transaction_notices':TransactionNoticeDelivery.objects.filter(state='held').count(),
        'uncertain_payments':SupportCheckout.objects.filter(checkout__syntheticcheckoutacceptance__attempt__state='uncertain').count(),
        'invitation_revocations':InvitationRevocation.objects.count(),
        'invitation_issues':InvitationIssue.objects.count(),
        'prepared_invitation_issues':InvitationIssue.objects.filter(invitation__isnull=True).count(),
        'discount_revocations':DiscountRevocation.objects.count(),
        'discount_issues':DiscountIssue.objects.count(),
        'prepared_discount_issues':DiscountIssue.objects.filter(discount__isnull=True).count(),
        'refund_reviews':RefundReview.objects.count(), 'refund_handoffs':RefundSupportHandoff.objects.count(),
        'uncertain_refunds':SyntheticOperationDispatch.objects.filter(operation__in=financial,operation__kind='refund',state='uncertain').count(),
    }


def assess_locked():
    """Internal caller holds the quarantined epoch and has drained effect scopes."""
    require(connection.vendor == 'postgresql' and connection.in_atomic_block)
    require(AccessEpoch.objects.filter(pk=1, quarantined=True).exists())
    require(drain_state(quarantined=True)['unfinished_effects'] == 0)
    try:
        root = settings.LOCAL_CHECKOUT_ARCHIVE_ROOT
        with (PreparedArchive(Path(root)) if root else nullcontext(None)) as archive:
            counts = _records(archive)
    except (ValueError, OSError, KeyError, TypeError, AttributeError, ObjectDoesNotExist):
        raise ShbError('shb_recovery_evidence_required', 503) from None
    return {'evidence_class':'local-synthetic', 'persisted_state_valid':True, 'counts':counts,
        'post_backup_completeness_established':False, 'actual_recovery_qualified':False,
        'retry_authorized':False, 'reopening_authorized':False}


def inspect_local_shb_recovery():
    """No HTTP route, writes, archive publication, mail or provider calls."""
    _guard()
    with transaction.atomic(durable=True):
        epoch = AccessEpoch.objects.select_for_update().filter(pk=1).first()
        require(epoch is not None and epoch.quarantined)
        return assess_locked()
