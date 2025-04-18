# Generated by Django 5.1.7 on 2025-03-16 08:34

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bus', '0015_alter_bus_driver'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bus',
            name='driver',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='bus.driver'),
        ),
        migrations.AlterField(
            model_name='bus',
            name='staff',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='bus.staff'),
        ),
    ]
