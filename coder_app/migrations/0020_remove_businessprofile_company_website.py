# Generated by Django 5.1.3 on 2024-12-27 15:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('coder_app', '0019_remove_customerprofile_date_of_birth'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='businessprofile',
            name='company_website',
        ),
    ]
