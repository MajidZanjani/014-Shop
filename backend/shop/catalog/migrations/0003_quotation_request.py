import uuid
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies=[('catalog','0002_draft_cart')]
    operations=[migrations.CreateModel(name='QuotationRequest',fields=[
        ('id',models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False,serialize=False)),
        ('request_id',models.UUIDField()),
        ('created_at',models.DateTimeField(auto_now_add=True)),
        ('cart',models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,to='catalog.draftcart')),
        ('snapshot',models.OneToOneField(on_delete=django.db.models.deletion.PROTECT,to='catalog.cartsnapshot')),
    ],options={'constraints':[models.UniqueConstraint(fields=('cart','request_id'),name='quotation_cart_request_unique')]}),
    migrations.CreateModel(name='QuotationRequestKey',fields=[
        ('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),
        ('request_id',models.UUIDField()),
        ('cart',models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,to='catalog.draftcart')),
        ('quotation',models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,to='catalog.quotationrequest')),
    ],options={'constraints':[models.UniqueConstraint(fields=('cart','request_id'),name='quotation_retry_key_unique')]})]
