# Generated by Django 5.1.4 on 2025-01-09 20:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('coder_app', '0028_alter_review_offer'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='offer',
            options={'ordering': ['-updated_at']},
        ),
    ]