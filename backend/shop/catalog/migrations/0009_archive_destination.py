from django.conf import settings
from django.db import migrations,models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies=[('catalog','0008_request_envelope_intent'),migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations=[
        migrations.CreateModel(name='ArchiveDestination',fields=[
            ('id',models.UUIDField(primary_key=True,editable=False,serialize=False)),
            ('device',models.PositiveBigIntegerField()),('inode',models.PositiveBigIntegerField()),
            ('manifest_sha256',models.CharField(max_length=64)),
            ('profile',models.CharField(max_length=32,default='local-prepared-v1')),
            ('created_at',models.DateTimeField(auto_now_add=True)),
            ('created_by',models.ForeignKey(to=settings.AUTH_USER_MODEL,on_delete=django.db.models.deletion.PROTECT,related_name='+')),
        ],options={'constraints':[
            models.UniqueConstraint(fields=['device','inode'],name='archive_destination_root_unique'),
            models.CheckConstraint(condition=models.Q(inode__gte=1,profile='local-prepared-v1',manifest_sha256__regex=r'^[0-9a-f]{64}$'),name='archive_destination_known_local'),
        ]}),
        migrations.AddField(model_name='requestarchiveintent',name='destination',field=models.ForeignKey(to='catalog.archivedestination',null=True,on_delete=django.db.models.deletion.PROTECT)),
        migrations.AddField(model_name='requestarchiveintent',name='destination_bound_by',field=models.ForeignKey(to=settings.AUTH_USER_MODEL,null=True,on_delete=django.db.models.deletion.PROTECT,related_name='+')),
        migrations.AddField(model_name='requestarchiveintent',name='destination_bound_at',field=models.DateTimeField(null=True)),
        migrations.AddField(model_name='requestarchiveintent',name='binding_staff_generation',field=models.UUIDField(null=True,editable=False)),
        migrations.AddField(model_name='requestarchiveintent',name='binding_mfa_verified_at',field=models.DateTimeField(null=True)),
        migrations.AddConstraint(model_name='requestarchiveintent',constraint=models.CheckConstraint(condition=models.Q(destination__isnull=True,destination_bound_by__isnull=True,destination_bound_at__isnull=True,binding_staff_generation__isnull=True,binding_mfa_verified_at__isnull=True)|models.Q(destination__isnull=False,destination_bound_by__isnull=False,destination_bound_at__isnull=False),name='request_archive_binding_present')),
        migrations.AddConstraint(model_name='requestarchiveintent',constraint=models.CheckConstraint(condition=models.Q(binding_staff_generation__isnull=True,binding_mfa_verified_at__isnull=True)|models.Q(binding_staff_generation__isnull=False,binding_mfa_verified_at__isnull=False),name='request_archive_binding_mfa')),
    ]
