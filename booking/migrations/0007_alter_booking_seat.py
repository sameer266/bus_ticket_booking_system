# Generated by Django 5.1.7 on 2025-03-17 11:32

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0006_alter_seat_unique_together_alter_booking_seat_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='booking',
            name='seat',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='booking.seat'),
        ),
    ]
