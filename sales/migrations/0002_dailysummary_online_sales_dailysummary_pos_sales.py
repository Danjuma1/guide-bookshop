from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='dailysummary',
            name='pos_sales',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name='dailysummary',
            name='online_sales',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
    ]
