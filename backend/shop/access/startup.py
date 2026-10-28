"""Read-only startup fence for an explicitly selected disposable local restore.

Select a fresh identity outside the restored database before starting any local
customer, staff or worker process. Settings import never initializes the DB.
Immutable fixture quarantine/release history is required for that identity.
Actual traffic/egress isolation and recovery qualification remain separate gates.
"""
import uuid
from django.conf import settings
from .models import LocalAccessRecoveryOperation


def restore_startup_pending(epoch):
    identity=getattr(settings,'LOCAL_RESTORE_ID',None)
    if identity is None:return False
    if (settings.SHOP_ENV not in ('local','synthetic') or type(identity) is not uuid.UUID
            or identity.version!=4 or identity.variant!=uuid.RFC_4122 or epoch is None):
        return True
    # Both records are immutable. An earlier restore's release cannot satisfy a
    # fresh external identity. A later ordinary hold still closes current access.
    return not (LocalAccessRecoveryOperation.objects.filter(pk=identity,action='quarantine').exists()
        and LocalAccessRecoveryOperation.objects.filter(action='release',basis_reset=identity).exists())
