# Generated by Django 5.1.7 on 2025-04-15 07:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_alter_otp_otp_created_at_alter_otp_phonenumber'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='profile_photo',
            field=models.ImageField(default='Default_pfp.jpg', upload_to='profiles'),
        ),
    ]
