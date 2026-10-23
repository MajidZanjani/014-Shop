from django.db import migrations, models
class Migration(migrations.Migration):
    dependencies=[('access','0002_staff_access'),('catalog','0006_quotation_business_scope')]
    operations=[migrations.AddField(model_name='staffquotationgrant',name='business_scope_version',field=models.PositiveIntegerField(default=0))]
