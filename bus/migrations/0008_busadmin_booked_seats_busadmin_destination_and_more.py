# Generated by Django 5.1.7 on 2025-03-09 07:33

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bus', '0007_remove_ticketcounter_phone_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='busadmin',
            name='booked_seats',
            field=models.PositiveIntegerField(default=0, help_text='Number of seats booked'),
        ),
        migrations.AddField(
            model_name='busadmin',
            name='destination',
            field=models.CharField(blank=True, help_text='Ending point of the journey (overrides route destination)', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='busadmin',
            name='driver',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='bus.driver'),
        ),
        migrations.AddField(
            model_name='busadmin',
            name='estimated_arrival',
            field=models.DateTimeField(blank=True, help_text='Estimated Arrival time', null=True),
        ),
        migrations.AddField(
            model_name='busadmin',
            name='last_updated',
            field=models.DateTimeField(auto_now=True, help_text='Timestamp of last update'),
        ),
        migrations.AddField(
            model_name='busadmin',
            name='price',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Ticket price for the bus journey', max_digits=8, null=True),
        ),
        migrations.AddField(
            model_name='busadmin',
            name='remaining_seats',
            field=models.PositiveIntegerField(default=0, help_text='Calculated remaining seats'),
        ),
        migrations.AddField(
            model_name='busadmin',
            name='source',
            field=models.CharField(blank=True, help_text='Starting point of the journey (overrides route source)', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='busadmin',
            name='bus',
            field=models.OneToOneField(blank=True, help_text='Bus assigned to this admin', null=True, on_delete=django.db.models.deletion.SET_NULL, to='bus.bus'),
        ),
    ]
