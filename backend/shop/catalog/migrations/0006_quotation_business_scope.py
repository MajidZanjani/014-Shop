from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies=[('catalog','0005_business_drafts')]
    operations=[
        migrations.AddField(model_name='quotationrequest',name='business_version',field=models.PositiveIntegerField(default=0)),
        migrations.AddField(model_name='quotationreview',name='business_version',field=models.PositiveIntegerField(default=0)),
        migrations.CreateModel(name='QuotationBusinessScope',fields=[
            ('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),
            ('version',models.PositiveIntegerField()),('created_at',models.DateTimeField(auto_now_add=True)),
            ('quotation',models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,to='catalog.quotationrequest')),
            ('business_snapshot',models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,to='catalog.businessdraftsnapshot')),
        ],options={'constraints':[
            models.UniqueConstraint(fields=('quotation','version'),name='quotation_business_scope_version'),
            models.CheckConstraint(condition=models.Q(version__gte=1),name='quotation_business_scope_positive')]}),
        migrations.CreateModel(name='QuotationBusinessKey',fields=[
            ('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),
            ('request_id',models.UUIDField()),('expected_version',models.PositiveIntegerField()),
            ('quotation',models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,to='catalog.quotationrequest')),
            ('scope',models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,to='catalog.quotationbusinessscope')),
        ],options={'constraints':[models.UniqueConstraint(fields=('quotation','request_id'),name='quotation_business_key_unique')]}),
    ]
