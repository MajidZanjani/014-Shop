"""Fail before opening a connection, including migration and test databases.

This is a temporary closed gate, not transaction attestation. Replace only with
an implementation covering application, worker, migration and operator writes.
"""
from django.core.exceptions import ImproperlyConfigured
from django.db.backends.postgresql.base import DatabaseWrapper as PostgreSQLWrapper


class DatabaseWrapper(PostgreSQLWrapper):
    def get_new_connection(self, conn_params):
        raise ImproperlyConfigured(
            'Shop database access is pending destination-guard integration and qualification'
        )
