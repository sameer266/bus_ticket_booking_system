# Generated by Django 5.1.7 on 2025-04-09 15:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0028_commission_created_at_and_more'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='rate',
            name='unique_rate',
        ),
        migrations.AddField(
            model_name='rate',
            name='rate_type',
            field=models.CharField(blank=True, choices=[('reservation', 'Reservation'), ('seat_booking', 'Seat Booking')], help_text='Type of rate (Reservation or Seat Booking)', max_length=20, null=True, unique=True),
        ),
    ]
