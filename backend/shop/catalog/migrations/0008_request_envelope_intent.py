from django.db.models.lookups import Exact
import uuid
from django.conf import settings
from django.db import migrations,models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies=[('catalog','0007_preparation_version'),migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations=[
        migrations.CreateModel(name='RequestEnvelope',fields=[
            ('id',models.UUIDField(primary_key=True,serialize=False,editable=False)),
            ('business_version',models.PositiveIntegerField(default=0)),
            ('schema_version',models.PositiveSmallIntegerField(default=1)),
            ('staff_generation',models.UUIDField(null=True,editable=False)),
            ('mfa_verified_at',models.DateTimeField(null=True)),
            ('payload',models.BinaryField(editable=False)),
            ('sha256',models.CharField(max_length=64)),
            ('byte_length',models.PositiveIntegerField()),
            ('created_at',models.DateTimeField(auto_now_add=True)),
            ('quotation',models.ForeignKey(to='catalog.quotationrequest',on_delete=django.db.models.deletion.PROTECT)),
            ('owner',models.ForeignKey(to=settings.AUTH_USER_MODEL,on_delete=django.db.models.deletion.PROTECT,related_name='+')),
            ('captured_by',models.ForeignKey(to=settings.AUTH_USER_MODEL,on_delete=django.db.models.deletion.PROTECT,related_name='+')),
        ],options={'constraints':[
            models.UniqueConstraint(fields=['quotation','business_version','schema_version'],name='request_envelope_semantic_unique'),
            models.CheckConstraint(condition=models.Q(schema_version=1,business_version__lte=1000000000),name='request_envelope_known_version'),
            models.CheckConstraint(condition=models.Q(byte_length__gte=1,byte_length__lte=131072),name='request_envelope_bounded_bytes'),
            models.CheckConstraint(condition=Exact(models.Func('payload',function='octet_length',output_field=models.IntegerField()),models.F('byte_length')),name='request_envelope_actual_length'),
            models.CheckConstraint(condition=models.Q(sha256__regex=r'^[0-9a-f]{64}$'),name='request_envelope_hash_shape'),
            models.CheckConstraint(condition=models.Q(staff_generation__isnull=True,mfa_verified_at__isnull=True)|models.Q(staff_generation__isnull=False,mfa_verified_at__isnull=False),name='request_envelope_staff_evidence'),
        ]}),
        migrations.CreateModel(name='RequestArchiveIntent',fields=[
            ('id',models.UUIDField(default=uuid.uuid4,editable=False,primary_key=True,serialize=False)),
            ('state',models.CharField(default='pending',max_length=16)),
            ('destination_profile',models.CharField(default='local-prepared-v1',max_length=32)),
            ('evidence_class',models.CharField(default='local-synthetic',max_length=32)),
            ('evidence_kind',models.CharField(default='prepared',max_length=16)),
            ('retention_qualified',models.BooleanField(default=False)),
            ('effects_authorized',models.BooleanField(default=False)),
            ('created_at',models.DateTimeField(auto_now_add=True)),
            ('envelope',models.OneToOneField(to='catalog.requestenvelope',on_delete=django.db.models.deletion.PROTECT)),
        ],options={'constraints':[
            models.CheckConstraint(condition=models.Q(state__in=['pending','held']),name='request_archive_unexecuted_state'),
            models.CheckConstraint(condition=models.Q(destination_profile='local-prepared-v1',evidence_class='local-synthetic',evidence_kind='prepared',retention_qualified=False,effects_authorized=False),name='request_archive_no_effects'),
        ]}),
    ]
