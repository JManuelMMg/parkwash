from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('parking', '0002_create_initial_spaces'),
    ]

    operations = [
        migrations.AddField(
            model_name='parkingspace',
            name='hourly_rate',
            field=models.DecimalField(decimal_places=2, default=20.00, max_digits=10, verbose_name='Tarifa por hora'),
        ),
        migrations.AddField(
            model_name='parkingspace',
            name='daily_rate',
            field=models.DecimalField(decimal_places=2, default=150.00, max_digits=10, verbose_name='Tarifa por día'),
        ),
    ] 