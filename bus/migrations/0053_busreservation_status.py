# Generated by Django 5.1.7 on 2025-03-30 08:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bus', '0052_bus_ticket_counter_busreservation_ticket_counter_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='busreservation',
            name='status',
            field=models.CharField(choices=[('booked', 'Booked'), ('cancelled', 'Cancelled'), ('pending', 'Pending')], default='pending', max_length=20),
        ),
    ]
