# Generated by Django 5.1.7 on 2025-03-31 08:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('custom_user', '0016_transportationcompany'),
    ]

    operations = [
        migrations.RenameField(
            model_name='transportationcompany',
            old_name='longitute',
            new_name='longitude',
        ),
    ]
