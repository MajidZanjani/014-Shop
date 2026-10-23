from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies=[('access','0003_business_scope_grant'),('catalog','0007_preparation_version'),migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations=[migrations.CreateModel(name='PreparationAssessment',fields=[
        ('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),
        ('version',models.PositiveIntegerField()),('request_id',models.UUIDField()),
        ('schema_version',models.PositiveSmallIntegerField(default=1)),
        ('business_version',models.PositiveIntegerField(default=0)),('review_version',models.PositiveIntegerField(default=0)),
        ('scope_digest',models.CharField(max_length=64)),('assessment_digest',models.CharField(max_length=64)),
        ('assessment',models.JSONField()),('staff_generation',models.UUIDField()),('mfa_verified_at',models.DateTimeField()),
        ('created_at',models.DateTimeField(auto_now_add=True)),
        ('quotation',models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,to='catalog.quotationrequest')),
        ('business_scope',models.ForeignKey(null=True,on_delete=django.db.models.deletion.PROTECT,to='catalog.quotationbusinessscope')),
        ('review',models.ForeignKey(null=True,on_delete=django.db.models.deletion.PROTECT,to='catalog.quotationreview')),
        ('captured_by',models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,to=settings.AUTH_USER_MODEL)),
    ],options={'constraints':[
        models.UniqueConstraint(fields=('quotation','version'),name='preparation_unique_version'),
        models.UniqueConstraint(fields=('quotation','request_id'),name='preparation_unique_request'),
        models.CheckConstraint(condition=models.Q(version__gte=1),name='preparation_positive_version'),
        models.CheckConstraint(condition=models.Q(business_version=0,business_scope__isnull=True)|models.Q(business_version__gt=0,business_scope__isnull=False),name='preparation_business_reference'),
        models.CheckConstraint(condition=models.Q(review_version=0,review__isnull=True)|models.Q(review_version__gt=0,review__isnull=False),name='preparation_review_reference'),
    ]})]
