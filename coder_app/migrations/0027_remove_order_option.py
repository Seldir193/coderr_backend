# Generated by Django 5.1.3 on 2025-01-01 10:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("coder_app", "0026_remove_order_offer_detail_id_remove_order_user_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="order",
            name="option",
        ),
    ]
