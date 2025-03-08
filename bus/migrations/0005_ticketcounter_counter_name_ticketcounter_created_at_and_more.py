# Generated by Django 5.1.7 on 2025-03-08 12:32

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bus', '0004_alter_driver_phone_number_alter_staff_phone_number_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='ticketcounter',
            name='counter_name',
            field=models.CharField(default='None', help_text='Name of Ticket Counter name', max_length=200),
        ),
        migrations.AddField(
            model_name='ticketcounter',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AlterField(
            model_name='ticketcounter',
            name='user',
            field=models.ForeignKey(limit_choices_to={'role': 'sub_admin'}, on_delete=django.db.models.deletion.CASCADE, related_name='ticket_counter', to=settings.AUTH_USER_MODEL),
        ),
    ]
