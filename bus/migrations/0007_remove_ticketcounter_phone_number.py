# Generated by Django 5.1.7 on 2025-03-08 13:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bus', '0006_remove_busadmin_address_remove_busadmin_company_name_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ticketcounter',
            name='phone_number',
        ),
    ]
