# Generated by Django 5.1.7 on 2025-03-26 08:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('custom_user', '0014_system_address'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='email',
            field=models.EmailField(blank=True, default='None', max_length=254, null=True),
        ),
    ]
