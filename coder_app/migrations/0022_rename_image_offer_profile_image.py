# Generated by Django 5.1.3 on 2024-12-29 20:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("coder_app", "0021_rename_profile_image_businessprofile_file"),
    ]

    operations = [
        migrations.RenameField(
            model_name="offer",
            old_name="image",
            new_name="profile_image",
        ),
    ]
