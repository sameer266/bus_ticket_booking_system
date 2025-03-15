# Generated by Django 5.1.7 on 2025-03-11 12:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bus', '0008_busadmin_booked_seats_busadmin_destination_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Feature',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
            ],
        ),
        migrations.AddField(
            model_name='bus',
            name='features',
            field=models.ManyToManyField(related_name='buses', to='bus.feature'),
        ),
    ]
