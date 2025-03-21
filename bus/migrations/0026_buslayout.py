# Generated by Django 5.1.7 on 2025-03-20 10:44

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bus', '0025_alter_busreservation_status'),
    ]

    operations = [
        migrations.CreateModel(
            name='BusLayout',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rows', models.PositiveIntegerField()),
                ('column', models.PositiveIntegerField()),
                ('aisle_column', models.PositiveIntegerField()),
                ('layout_data', models.JSONField(blank=True, default=list)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('bus', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bus.bus')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
