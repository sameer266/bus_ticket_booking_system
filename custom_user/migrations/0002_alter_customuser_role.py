# Generated by Django 5.1.7 on 2025-03-08 12:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('custom_user', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='role',
            field=models.CharField(choices=[('admin', 'Admin User'), ('sub_admin', 'Sub Admin'), ('bus_admin', 'Bus Admin User'), ('customer', 'Normal User')], default='customer', max_length=20),
        ),
    ]
