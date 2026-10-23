from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies=[('catalog','0004_quotation_reviews'),migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations=[
        migrations.CreateModel(name='BusinessDraft',fields=[
            ('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),
            ('version',models.PositiveIntegerField(default=0)),
            ('owner',models.OneToOneField(on_delete=django.db.models.deletion.PROTECT,to=settings.AUTH_USER_MODEL)),
        ]),
        migrations.CreateModel(name='BusinessDraftSnapshot',fields=[
            ('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),
            ('version',models.PositiveIntegerField()),('request_id',models.UUIDField()),
            ('schema_version',models.PositiveSmallIntegerField()),('source_sha256',models.CharField(max_length=64)),
            ('submission_digest',models.CharField(max_length=64)),('details',models.JSONField()),('evaluation',models.JSONField()),
            ('created_at',models.DateTimeField(auto_now_add=True)),
            ('draft',models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,to='catalog.businessdraft')),
        ],options={'constraints':[
            models.UniqueConstraint(fields=('draft','version'),name='business_snapshot_unique_version'),
            models.UniqueConstraint(fields=('draft','request_id'),name='business_snapshot_unique_request'),
            models.CheckConstraint(condition=models.Q(version__gte=1),name='business_snapshot_positive_version'),
        ]}),
    ]
