# Generated by Django 5.1.7 on 2025-05-12 19:36

import phonenumber_field.modelfields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0013_location_is_choose'),
    ]

    operations = [
        migrations.AlterField(
            model_name='otp',
            name='phonenumber',
            field=phonenumber_field.modelfields.PhoneNumberField(db_index=True, max_length=128, region='IR'),
        ),
    ]
