"""Closed structured events: never serialize messages, exceptions or request data."""
import json
import logging
import re
import uuid

EVENTS = frozenset({'health.live', 'health.ready', 'startup.rejected', 'adapter.failed'})


class SafeFormatter(logging.Formatter):
    def format(self, record):
        event = getattr(record, 'event', None)
        event = event if isinstance(event, str) and event in EVENTS else 'runtime.event'
        status = getattr(record, 'status_code', None)
        status = status if type(status) is int and 100 <= status <= 599 else None
        correlation = getattr(record, 'correlation_id', None)
        correlation = correlation if isinstance(correlation, str) and re.fullmatch('[0-9a-f]{32}', correlation) else None
        return json.dumps({'event': event, 'status': status, 'correlation_id': correlation}, separators=(',', ':'))


def safe_event(event, status):
    # Generate identifiers locally; do not trust inbound headers/paths as correlation data.
    logging.getLogger('shop').info('safe event', extra={
        'event': event, 'status_code': status, 'correlation_id': uuid.uuid4().hex})
