# Generated by Django 5.1.7 on 2025-03-28 06:24

import django.db.models.deletion
import django.db.models.expressions
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bus', '0051_alter_driver_driver_profile'),
    ]

    operations = [
        migrations.AddField(
            model_name='bus',
            name='ticket_counter',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='bus.ticketcounter'),
        ),
        migrations.AddField(
            model_name='busreservation',
            name='ticket_counter',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='bus.ticketcounter'),
        ),
        migrations.AddField(
            model_name='driver',
            name='ticket_counter',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='bus.ticketcounter'),
        ),
        migrations.AddField(
            model_name='staff',
            name='ticket_counter',
            field=models.ForeignKey(null=True, on_delete=django.db.models.expressions.Case, to='bus.ticketcounter'),
        ),
    ]
