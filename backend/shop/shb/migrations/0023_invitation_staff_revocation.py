"""Exact invitation staff assignments and retained revocation audit."""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations,models


class Migration(migrations.Migration):
    dependencies=[('shb','0022_refund_review_provenance'),migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations=[
        migrations.CreateModel(name='InvitationStaffGrant',fields=[
            ('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),
            ('invitation',models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,to='shb.invitation')),
            ('user',models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,to=settings.AUTH_USER_MODEL)),
        ],options={'constraints':[models.UniqueConstraint(fields=('user','invitation'),name='shb_invitation_staff_once')]}),
        migrations.CreateModel(name='InvitationRevocation',fields=[
            ('id',models.UUIDField(editable=False,primary_key=True,serialize=False)),
            ('request_id',models.UUIDField(editable=False)),
            ('revoked_at',models.DateTimeField(editable=False)),
            ('payload',models.JSONField(editable=False)),
            ('sha256',models.CharField(editable=False,max_length=64)),
            ('archive_receipt',models.JSONField(editable=False)),
            ('invitation',models.OneToOneField(on_delete=django.db.models.deletion.PROTECT,to='shb.invitation')),
        ],options={'constraints':[models.CheckConstraint(condition=models.Q(sha256__regex=r'^[a-f0-9]{64}$') & ~models.Q(archive_receipt={}),name='shb_invitation_revocation_archive')]}),
    ]
