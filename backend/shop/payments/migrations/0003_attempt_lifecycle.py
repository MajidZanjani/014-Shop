from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('payments', '0002_syntheticpaymentattempt')]
    operations = [
        migrations.AddField(model_name='syntheticpaymentattempt', name='expires_at', field=models.DateTimeField(null=True)),
        migrations.AddField(model_name='syntheticpaymentattempt', name='stopped_at', field=models.DateTimeField(null=True)),
        migrations.RemoveConstraint(model_name='syntheticpaymentattempt', name='synthetic_attempt_state'),
        migrations.AddConstraint(
            model_name='syntheticpaymentattempt',
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(state__in=('prepared', 'uncertain'), stopped_at__isnull=True,
                             provider_operation_id__isnull=True, provider_status='')
                    | models.Q(state='observed', stopped_at__isnull=True, provider_operation_id__isnull=False,
                               provider_status__in=('authorized', 'captured', 'declined', 'pending'))
                    | models.Q(state='cancelled', stopped_at__isnull=False,
                               provider_operation_id__isnull=True, provider_status='')
                    | models.Q(state='expired', expires_at__isnull=False, stopped_at__isnull=False,
                               stopped_at__gte=models.F('expires_at'), provider_operation_id__isnull=True,
                               provider_status='')
                ),
                name='synthetic_attempt_state',
            ),
        ),
    ]
