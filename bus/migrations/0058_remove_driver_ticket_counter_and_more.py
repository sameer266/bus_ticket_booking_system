# Generated by Django 5.1.7 on 2025-04-02 03:24

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bus', '0057_remove_bus_is_running'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='driver',
            name='ticket_counter',
        ),
        migrations.RemoveField(
            model_name='staff',
            name='ticket_counter',
        ),
    ]
