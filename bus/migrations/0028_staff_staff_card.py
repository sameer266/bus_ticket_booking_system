# Generated by Django 5.1.7 on 2025-03-21 08:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bus', '0027_alter_buslayout_bus'),
    ]

    operations = [
        migrations.AddField(
            model_name='staff',
            name='staff_card',
            field=models.ImageField(blank=True, null=True, upload_to='staff_card/'),
        ),
    ]
