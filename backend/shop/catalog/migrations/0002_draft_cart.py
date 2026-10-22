import uuid
from django.conf import settings
from django.db import migrations,models
import django.db.models.deletion
class Migration(migrations.Migration):
    dependencies=[('catalog','0001_initial'),migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations=[
        migrations.CreateModel(name='DraftCart',fields=[
            ('id',models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False,serialize=False)),
            ('version',models.PositiveIntegerField(default=0)),
            ('owner',models.OneToOneField(on_delete=django.db.models.deletion.PROTECT,to=settings.AUTH_USER_MODEL)),
        ]),
        migrations.CreateModel(name='CartSnapshot',fields=[
            ('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),
            ('version',models.PositiveIntegerField()),('request_id',models.UUIDField()),
            ('catalog_revision',models.CharField(max_length=64)),('lines',models.JSONField()),('evaluation',models.JSONField()),
            ('created_at',models.DateTimeField(auto_now_add=True)),
            ('cart',models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,to='catalog.draftcart')),
        ],options={'constraints':[
            models.UniqueConstraint(fields=('cart','version'),name='cart_snapshot_unique_version'),
            models.UniqueConstraint(fields=('cart','request_id'),name='cart_snapshot_unique_request'),
            models.CheckConstraint(condition=models.Q(version__gte=1),name='cart_snapshot_positive_version'),
        ]}),
    ]
