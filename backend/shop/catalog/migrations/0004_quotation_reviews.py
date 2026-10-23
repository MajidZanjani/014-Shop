from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies=[('catalog','0003_quotation_request'),migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations=[
        migrations.AddField(model_name='quotationrequest',name='review_version',field=models.PositiveIntegerField(default=0)),
        migrations.CreateModel(name='QuotationReview',fields=[
            ('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),
            ('version',models.PositiveIntegerField()),('request_id',models.UUIDField()),
            ('snapshot_digest',models.CharField(max_length=64)),
            ('decision',models.CharField(max_length=32,choices=[('needs_information','Needs scope clarification'),('ready_for_commercial_review','Ready for commercial review (offer not approved)'),('declined','Declined request')])),
            ('reviewer_generation',models.UUIDField()),('mfa_verified_at',models.DateTimeField()),
            ('created_at',models.DateTimeField(auto_now_add=True)),
            ('quotation',models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,to='catalog.quotationrequest')),
            ('reviewer',models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,to=settings.AUTH_USER_MODEL)),
        ],options={'constraints':[
            models.UniqueConstraint(fields=('quotation','version'),name='quotation_review_unique_version'),
            models.UniqueConstraint(fields=('quotation','request_id'),name='quotation_review_unique_request'),
            models.CheckConstraint(condition=models.Q(version__gte=1),name='quotation_review_positive_version'),
            models.CheckConstraint(condition=models.Q(decision__in=['needs_information','ready_for_commercial_review','declined']),name='quotation_review_known_decision'),
        ]}),
    ]
