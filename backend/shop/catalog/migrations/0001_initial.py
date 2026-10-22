import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
class Migration(migrations.Migration):
    initial=True
    dependencies=[migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations=[migrations.CreateModel(name='ConfigurationDraft',fields=[
        ('id',models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False,serialize=False)),
        ('request_id',models.UUIDField()),('revision',models.CharField(max_length=64)),
        ('configuration',models.JSONField()),('evaluation',models.JSONField()),
        ('created_at',models.DateTimeField(auto_now_add=True)),
        ('owner',models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,to=settings.AUTH_USER_MODEL)),
    ],options={'constraints':[models.UniqueConstraint(fields=('owner','request_id'),name='catalog_owner_request_unique')]})]
