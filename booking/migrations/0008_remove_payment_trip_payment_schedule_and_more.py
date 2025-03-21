# Generated by Django 5.1.7 on 2025-03-17 11:52

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0007_alter_booking_seat'),
        ('route', '0010_customerreview_route'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='payment',
            name='trip',
        ),
        migrations.AddField(
            model_name='payment',
            name='schedule',
            field=models.ForeignKey(default=1, help_text='The Schedule for which the payment was made', on_delete=django.db.models.deletion.CASCADE, to='route.schedule'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='booking',
            name='schedule',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='route.schedule'),
        ),
    ]
