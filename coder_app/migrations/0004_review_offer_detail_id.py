# Generated by Django 5.1.3 on 2024-12-09 21:17

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("coder_app", "0003_review_offer"),
    ]

    operations = [
        migrations.AddField(
            model_name="review",
            name="offer_detail_id",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="coder_app.offerdetail",
            ),
        ),
    ]
