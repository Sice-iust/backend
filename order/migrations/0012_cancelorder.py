# Generated by Django 5.1.7 on 2025-05-29 19:12

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0011_rename_reciver_phon_order_reciver_phone'),
    ]

    operations = [
        migrations.CreateModel(
            name='CancelOrder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reason', models.TextField()),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='orders', to='order.order')),
            ],
        ),
    ]
