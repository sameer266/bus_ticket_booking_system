# Generated by Django 5.1.7 on 2025-03-19 11:29

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bus', '0021_busadmin_route'),
        ('route', '0010_customerreview_route'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='busadmin',
            name='route',
        ),
        migrations.AddField(
            model_name='bus',
            name='route',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='route.route'),
        ),
    ]
