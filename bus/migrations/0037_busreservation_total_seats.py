# Generated by Django 5.1.7 on 2025-03-23 05:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bus', '0036_remove_busreservation_user_alter_bus_is_active_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='busreservation',
            name='total_seats',
            field=models.PositiveIntegerField(default=35),
        ),
    ]
