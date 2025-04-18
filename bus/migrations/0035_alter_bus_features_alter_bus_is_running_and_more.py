# Generated by Django 5.1.7 on 2025-03-22 10:29

import multiselectfield.db.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bus', '0034_alter_busreservation_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bus',
            name='features',
            field=multiselectfield.db.fields.MultiSelectField(blank=True, choices=[('ac', 'AC'), ('charging', 'Charging'), ('fan', 'Fan'), ('wifi', 'WiFi')], max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='bus',
            name='is_running',
            field=models.BooleanField(default=False, help_text='Indicates if the bus is currently running'),
        ),
        migrations.AlterField(
            model_name='busadmin',
            name='destination',
            field=models.CharField(blank=True, help_text='Ending point of the journey', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='busadmin',
            name='price',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Ticket price', max_digits=8, null=True),
        ),
        migrations.AlterField(
            model_name='busadmin',
            name='source',
            field=models.CharField(blank=True, help_text='Starting point of the journey', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='ticketcounter',
            name='counter_name',
            field=models.CharField(default='None', help_text='Name of Ticket Counter', max_length=200),
        ),
    ]
