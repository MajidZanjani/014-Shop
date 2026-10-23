from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies=[('catalog','0006_quotation_business_scope')]
    operations=[migrations.AddField(model_name='quotationrequest',name='preparation_version',field=models.PositiveIntegerField(default=0))]
