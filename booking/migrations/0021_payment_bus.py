# Generated by Django 5.1.7 on 2025-03-26 07:34

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0020_payment_user'),
        ('bus', '0049_alter_buslayout_bus'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='bus',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='bus.bus'),
        ),
    ]
