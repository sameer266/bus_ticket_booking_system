# Generated by Django 5.1.7 on 2025-03-24 07:25

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0012_booking_bus_reserve_alter_booking_seat'),
        ('bus', '0044_rename_reservation_date_busreservation_end_date_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='booking',
            name='bus',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='booking', to='bus.bus'),
        ),
    ]
