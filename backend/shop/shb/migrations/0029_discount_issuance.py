"""Separate commercial issuance scope and durable digest-only discount intent."""
import uuid
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations,models


class Migration(migrations.Migration):
    dependencies=[('shb','0028_discount_revocation_provenance'),migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations=[
        migrations.CreateModel(name='DiscountIssuanceScope',fields=[
            ('id',models.UUIDField(default=uuid.uuid4,editable=False,primary_key=True,serialize=False)),
            ('percentage_bps',models.PositiveSmallIntegerField()),
            ('fpga_allowed',models.BooleanField(default=False)),('asic_allowed',models.BooleanField(default=False)),
            ('use_limit',models.PositiveSmallIntegerField(default=1)),
            ('claim_period_days',models.PositiveSmallIntegerField()),
            ('evidence_class',models.CharField(default='local-synthetic',editable=False,max_length=32)),
            ('created_at',models.DateTimeField(default=django.utils.timezone.now,editable=False)),
            ('enabled',models.BooleanField(default=True)),
            ('customer',models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,related_name='+',to=settings.AUTH_USER_MODEL)),
            ('registered_by',models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,related_name='+',to=settings.AUTH_USER_MODEL)),
        ],options={'constraints':[
            models.CheckConstraint(condition=models.Q(fpga_allowed=True)|models.Q(asic_allowed=True),name='shb_discount_issue_scope_modes'),
            models.CheckConstraint(condition=models.Q(percentage_bps__gte=1,percentage_bps__lte=9999),name='shb_discount_issue_scope_percentage'),
            models.CheckConstraint(condition=models.Q(use_limit__gte=1,use_limit__lte=100),name='shb_discount_issue_scope_use_limit'),
            models.CheckConstraint(condition=models.Q(claim_period_days__gte=1,claim_period_days__lte=365),name='shb_discount_issue_scope_claim_period'),
            models.CheckConstraint(condition=models.Q(evidence_class='local-synthetic'),name='shb_discount_issue_scope_synthetic')]}),
        migrations.CreateModel(name='DiscountIssueGrant',fields=[
            ('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),
            ('scope',models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,to='shb.discountissuancescope')),
            ('user',models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,to=settings.AUTH_USER_MODEL)),
        ],options={'constraints':[models.UniqueConstraint(fields=('user','scope'),name='shb_discount_issue_grant_once')]}),
        migrations.CreateModel(name='DiscountIssue',fields=[
            ('id',models.UUIDField(editable=False,primary_key=True,serialize=False)),
            ('request_id',models.UUIDField(editable=False)),('created_at',models.DateTimeField(editable=False)),
            ('payload',models.JSONField(editable=False)),('sha256',models.CharField(editable=False,max_length=64)),
            ('archive_receipt',models.JSONField(default=dict,editable=False)),
            ('scope',models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,to='shb.discountissuancescope')),
            ('discount',models.OneToOneField(null=True,on_delete=django.db.models.deletion.PROTECT,related_name='+',to='shb.discountcode')),
        ],options={'constraints':[
            models.UniqueConstraint(fields=('scope','request_id'),name='shb_discount_issue_retry_once'),
            models.CheckConstraint(condition=models.Q(sha256__regex=r'^[a-f0-9]{64}$') &
                (models.Q(discount__isnull=True,archive_receipt={}) | (models.Q(discount__isnull=False)&~models.Q(archive_receipt={}))),name='shb_discount_issue_publication_archive')]}),
    ]
