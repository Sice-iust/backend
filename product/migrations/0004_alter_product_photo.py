# Generated by Django 5.1.7 on 2025-03-26 11:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0003_remove_discount_product_product_discount_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='photo',
            field=models.ImageField(upload_to='product'),
        ),
    ]
