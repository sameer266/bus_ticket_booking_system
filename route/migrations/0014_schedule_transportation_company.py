# Generated by Django 5.1.7 on 2025-03-31 09:41

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('custom_user', '0018_transportationcompany_user'),
        ('route', '0013_schedule_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='schedule',
            name='transportation_company',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='custom_user.transportationcompany'),
        ),
    ]
