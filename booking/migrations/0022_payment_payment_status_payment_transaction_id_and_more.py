# Generated by Django 5.1.7 on 2025-03-27 09:22

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0021_payment_bus'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='payment_status',
            field=models.CharField(choices=[('pending', 'Pending'), ('completed', 'Completed'), ('failed', 'Failed')], default='pending', max_length=20),
        ),
        migrations.AddField(
            model_name='payment',
            name='transaction_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='booking',
            name='payment',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='booking.payment'),
        ),
    ]
