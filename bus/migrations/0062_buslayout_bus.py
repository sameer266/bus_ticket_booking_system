# Generated by Django 5.1.7 on 2025-04-11 06:11

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bus', '0061_remove_buslayout_bus_buslayout_schedule'),
    ]

    operations = [
        migrations.AddField(
            model_name='buslayout',
            name='bus',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='bus.bus'),
        ),
    ]
