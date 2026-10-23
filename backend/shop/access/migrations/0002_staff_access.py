import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies=[('access','0001_initial'),('catalog','0003_quotation_request'),migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations=[
        migrations.CreateModel(name='StaffCredential',fields=[
            ('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),
            ('generation',models.UUIDField(default=uuid.uuid4)),('enabled',models.BooleanField(default=True)),
            ('user',models.OneToOneField(on_delete=django.db.models.deletion.PROTECT,to=settings.AUTH_USER_MODEL)),
        ]),
        migrations.CreateModel(name='StaffLoginThrottle',fields=[
            ('identity_digest',models.CharField(max_length=64,primary_key=True,serialize=False)),
            ('window_start',models.DateTimeField()),('attempts',models.PositiveSmallIntegerField(default=0)),
        ]),
        migrations.CreateModel(name='StaffChallenge',fields=[
            ('id',models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False,serialize=False)),
            ('generation',models.UUIDField()),('code_digest',models.CharField(max_length=64)),
            ('binding_digest',models.CharField(max_length=64)),('expires_at',models.DateTimeField()),
            ('attempts',models.PositiveSmallIntegerField(default=0)),('consumed_at',models.DateTimeField(null=True)),
            ('credential',models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,to='access.staffcredential')),
        ]),
        migrations.CreateModel(name='StaffQuotationGrant',fields=[
            ('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),
            ('user',models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,to=settings.AUTH_USER_MODEL)),
            ('quotation',models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,to='catalog.quotationrequest')),
        ],options={'constraints':[models.UniqueConstraint(fields=('user','quotation'),name='staff_quotation_reviewer_unique')]}),
    ]
