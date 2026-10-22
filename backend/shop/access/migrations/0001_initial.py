import uuid
from django.conf import settings
from django.db import migrations,models
import django.db.models.deletion
class Migration(migrations.Migration):
    initial=True
    dependencies=[migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations=[
        migrations.CreateModel(name='CustomerIdentity',fields=[
            ('id',models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False,serialize=False)),
            ('email',models.EmailField(max_length=160,unique=True)),('verified_at',models.DateTimeField()),
            ('user',models.OneToOneField(on_delete=django.db.models.deletion.PROTECT,to=settings.AUTH_USER_MODEL)),
        ]),
        migrations.CreateModel(name='VerificationChallenge',fields=[
            ('id',models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False,serialize=False)),
            ('email',models.EmailField(max_length=160)),('code_digest',models.CharField(max_length=64)),
            ('binding_digest',models.CharField(max_length=64)),('created_at',models.DateTimeField(auto_now_add=True)),
            ('expires_at',models.DateTimeField()),('attempts',models.PositiveSmallIntegerField(default=0)),('consumed_at',models.DateTimeField(null=True)),
        ]),
        migrations.CreateModel(name='VerificationThrottle',fields=[
            ('email_digest',models.CharField(max_length=64,primary_key=True,serialize=False)),
            ('window_start',models.DateTimeField()),('requests',models.PositiveSmallIntegerField(default=0)),
        ]),
    ]
