"""Add SHB scope to the shared checkout; one discount target per held use."""
import django.db.models.deletion
from django.db import migrations,models


class Migration(migrations.Migration):
    dependencies=[('catalog','0025_shb_business_scope'),('shb','0006_review_release_provenance')]
    operations=[
        migrations.CreateModel(name='SupportCheckout',fields=[
            ('checkout',models.OneToOneField(on_delete=django.db.models.deletion.PROTECT,primary_key=True,serialize=False,to='catalog.syntheticcheckout')),
            ('request_id',models.UUIDField(editable=False)),
            ('submission_sha256',models.CharField(editable=False,max_length=64)),
            ('review_sha256',models.CharField(editable=False,max_length=64)),
            ('session_digest',models.CharField(editable=False,max_length=64)),
            ('invitation',models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,to='shb.invitation')),
        ],options={'constraints':[
            models.UniqueConstraint(fields=('invitation','request_id'),name='shb_checkout_retry'),
            models.CheckConstraint(condition=models.Q(submission_sha256__regex=r'^[a-f0-9]{64}$',review_sha256__regex=r'^[a-f0-9]{64}$',session_digest__regex=r'^[a-f0-9]{64}$'),name='shb_checkout_digests')]}),
        migrations.AlterField(model_name='discountreservation',name='request',field=models.OneToOneField(null=True,on_delete=django.db.models.deletion.PROTECT,to='shb.supportrequest')),
        migrations.AddField(model_name='discountreservation',name='checkout',field=models.OneToOneField(null=True,on_delete=django.db.models.deletion.PROTECT,to='catalog.syntheticcheckout')),
        migrations.AddConstraint(model_name='discountreservation',constraint=models.CheckConstraint(
            condition=models.Q(request__isnull=False,checkout__isnull=True)|models.Q(request__isnull=True,checkout__isnull=False),name='shb_discount_one_claim_target')),
    ]
