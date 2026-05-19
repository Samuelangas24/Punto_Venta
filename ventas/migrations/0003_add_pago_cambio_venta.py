from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ventas', '0002_alter_detalleventa_options_alter_venta_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='venta',
            name='monto_pagado',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name='venta',
            name='cambio',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
    ]
