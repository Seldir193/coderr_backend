# Generated by Django 5.1.3 on 2024-12-30 14:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("coder_app", "0023_rename_profile_image_offer_file"),
    ]

    operations = [
        migrations.RenameField(
            model_name="offer",
            old_name="file",
            new_name="image",
        ),
    ]
