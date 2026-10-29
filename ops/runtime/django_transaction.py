"""Multi-statement ORM precursor; no connection opening or production enablement.

Trusted callers must separately bind expected/runtime_probe to approved records
and qualify transport/roles. This context is not automatic all-write enforcement
or a SQL sandbox. Existing production backend continues to deny connection opens.
"""
import contextlib
import control
import database
from guard import require,validate_database_identity
from psycopg.pq import TransactionStatus


@contextlib.contextmanager
def guarded_atomic(wrapper, expected, runtime_probe, *, observer_owner=None):
    """Own one Django atomic transaction and retain admission through its exit.

    Already-connected Psycopg wrapper only. Never reconnect, change credentials,
    retry uncertain commits, run deferred callbacks or accept an outer transaction.
    Caller retains connection ownership; failures propagate without diagnostics.
    """
    from django.db import connections,transaction
    if observer_owner is None:
        observe=database.observe_database
    else:
        from application_observer import observe_application_database
        def observe(cursor,runtime):
            return observe_application_database(cursor,runtime,observer_owner)
    validate_database_identity(expected,expected)
    expected=dict(expected)
    require(callable(runtime_probe) and wrapper.vendor=='postgresql'
            and connections[wrapper.alias] is wrapper and wrapper.connection is not None)
    raw=wrapper.connection
    require(not wrapper.in_atomic_block and not wrapper.needs_rollback
            and wrapper.get_autocommit() is True and raw.autocommit is True
            and raw.info.transaction_status==TransactionStatus.IDLE
            and not wrapper.run_on_commit)
    with control.admission():
        # No admission gap between observation and commit/rollback. Django's
        # durable=True rejects accidental outer nesting; internal savepoints
        # remain Django's responsibility, and the final guard can still abort.
        with transaction.atomic(using=wrapper.alias,durable=True):
            require(wrapper.connection is raw and raw.autocommit is False)
            with raw.cursor() as cursor:
                cursor.execute('SET LOCAL search_path = pg_catalog, public',prepare=True)
                cursor.execute("SET LOCAL statement_timeout = '2s'",prepare=True)
                cursor.execute("SET LOCAL lock_timeout = '1s'",prepare=True)
                control.check_admission()
                baseline=runtime_probe()
                validate_database_identity(expected,observe(cursor,baseline))
            yield wrapper
            require(wrapper.connection is raw and not wrapper.needs_rollback
                    and wrapper.in_atomic_block and raw.autocommit is False
                    and raw.info.transaction_status==TransactionStatus.INTRANS
                    and not wrapper.run_on_commit)
            control.check_admission()
            current=runtime_probe()
            require(current==baseline)
            with raw.cursor() as cursor:
                validate_database_identity(expected,observe(cursor,current))
            control.check_admission()
        # The outer admission context performs its final check only after
        # commit/rollback and Django autocommit restoration. A commit exception
        # is uncertain: no success report or implicit retry is provided.


def guarded_application_atomic(wrapper, expected, runtime_probe, *, observer_owner):
    """Select only the pinned restricted-role observer; no transport/all-write claim."""
    require(observer_owner is not None)
    return guarded_atomic(wrapper,expected,runtime_probe,observer_owner=observer_owner)
