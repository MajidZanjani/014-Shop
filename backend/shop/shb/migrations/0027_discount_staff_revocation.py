"""Exact discount revocation assignments and recoverable decision audit."""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations,models


class Migration(migrations.Migration):
    dependencies=[('shb','0026_invitation_issue_provenance'),migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations=[
        migrations.CreateModel(name='DiscountStaffGrant',fields=[
            ('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),
            ('discount',models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,to='shb.discountcode')),
            ('user',models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,to=settings.AUTH_USER_MODEL)),
        ],options={'constraints':[models.UniqueConstraint(fields=('user','discount'),name='shb_discount_staff_once')]}),
        migrations.CreateModel(name='DiscountRevocation',fields=[
            ('id',models.UUIDField(editable=False,primary_key=True,serialize=False)),
            ('request_id',models.UUIDField(editable=False)),('revoked_at',models.DateTimeField(editable=False)),
            ('payload',models.JSONField(editable=False)),('sha256',models.CharField(editable=False,max_length=64)),
            ('archive_receipt',models.JSONField(editable=False)),
            ('discount',models.OneToOneField(on_delete=django.db.models.deletion.PROTECT,to='shb.discountcode')),
        ],options={'constraints':[models.CheckConstraint(condition=models.Q(sha256__regex=r'^[a-f0-9]{64}$') & ~models.Q(archive_receipt={}),name='shb_discount_revocation_archive')]}),
    ]
