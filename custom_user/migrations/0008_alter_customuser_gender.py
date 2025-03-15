# Generated by Django 5.1.7 on 2025-03-14 08:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('custom_user', '0007_alter_customuser_gender'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='gender',
            field=models.CharField(blank=True, choices=[('male', 'Male'), ('female', 'Female'), ('others', 'Others')], max_length=50, null=True),
        ),
    ]
