# Generated by Django 5.1.3 on 2024-12-17 09:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("coder_app", "0017_rename_profile_image_businessprofile_file"),
    ]

    operations = [
        migrations.RenameField(
            model_name="businessprofile",
            old_name="file",
            new_name="profile_image",
        ),
    ]
