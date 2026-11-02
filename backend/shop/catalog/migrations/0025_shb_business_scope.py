"""Keep the SHB minimum form out of the historical IP licence questionnaire."""
import django.db.models.deletion
from django.db import migrations,models


class Migration(migrations.Migration):
    dependencies=[('catalog','0024_syntheticsupportcontext')]
    operations=[
        migrations.AlterField(model_name='syntheticcheckout',name='business_snapshot',
            field=models.ForeignKey(null=True,on_delete=django.db.models.deletion.PROTECT,to='catalog.businessdraftsnapshot')),
        migrations.AddConstraint(model_name='syntheticcheckout',constraint=models.CheckConstraint(
            condition=models.Q(business_snapshot__isnull=False)|models.Q(snapshot__release='shb-1.1',snapshot__release__isnull=False),
            name='checkout_business_or_shb')),
    ]
