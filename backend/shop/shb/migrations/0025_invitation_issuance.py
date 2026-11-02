"""Separate eligibility/issuance assignment and durable digest-only issue intent."""
import uuid
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations,models


class Migration(migrations.Migration):
    dependencies=[('shb','0024_invitation_revocation_provenance'),migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations=[
        migrations.CreateModel(name='InvitationIssuanceScope',fields=[
            ('id',models.UUIDField(default=uuid.uuid4,editable=False,primary_key=True,serialize=False)),
            ('company_name',models.CharField(max_length=200)),
            ('project_reference',models.CharField(blank=True,max_length=160)),
            ('eligibility_reference',models.CharField(max_length=160)),
            ('fpga_eligible',models.BooleanField(default=False)),('asic_allowed',models.BooleanField(default=False)),
            ('evidence_class',models.CharField(default='local-synthetic',editable=False,max_length=32)),
            ('created_at',models.DateTimeField(default=django.utils.timezone.now,editable=False)),
            ('enabled',models.BooleanField(default=True)),
            ('customer',models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,related_name='+',to=settings.AUTH_USER_MODEL)),
            ('registered_by',models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,related_name='+',to=settings.AUTH_USER_MODEL)),
        ],options={'constraints':[
            models.CheckConstraint(condition=models.Q(fpga_eligible=True)|models.Q(asic_allowed=True),name='shb_issue_scope_modes'),
            models.CheckConstraint(condition=models.Q(evidence_class='local-synthetic',eligibility_reference__regex=r'\S',company_name__regex=r'\S'),name='shb_issue_scope_synthetic')]}),
        migrations.CreateModel(name='InvitationIssueGrant',fields=[
            ('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),
            ('scope',models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,to='shb.invitationissuancescope')),
            ('user',models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,to=settings.AUTH_USER_MODEL)),
        ],options={'constraints':[models.UniqueConstraint(fields=('user','scope'),name='shb_issue_grant_once')]}),
        migrations.CreateModel(name='InvitationIssue',fields=[
            ('id',models.UUIDField(editable=False,primary_key=True,serialize=False)),
            ('request_id',models.UUIDField(editable=False)),('created_at',models.DateTimeField(editable=False)),
            ('payload',models.JSONField(editable=False)),('sha256',models.CharField(editable=False,max_length=64)),
            ('archive_receipt',models.JSONField(default=dict,editable=False)),
            ('scope',models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,to='shb.invitationissuancescope')),
            ('invitation',models.OneToOneField(null=True,on_delete=django.db.models.deletion.PROTECT,related_name='+',to='shb.invitation')),
            ('replaces',models.OneToOneField(null=True,on_delete=django.db.models.deletion.PROTECT,related_name='+',to='shb.invitation')),
        ],options={'constraints':[
            models.UniqueConstraint(fields=('scope','request_id'),name='shb_issue_retry_once'),
            models.CheckConstraint(condition=models.Q(sha256__regex=r'^[a-f0-9]{64}$') &
                (models.Q(invitation__isnull=True,archive_receipt={}) | (models.Q(invitation__isnull=False)&~models.Q(archive_receipt={}))),name='shb_issue_publication_archive')]}),
    ]
