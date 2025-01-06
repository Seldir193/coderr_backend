# Generated by Django 5.1.3 on 2025-01-01 21:35

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coder_app', '0027_remove_order_option'),
    ]

    operations = [
        migrations.AlterField(
            model_name='review',
            name='offer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='offer_reviews', to='coder_app.offer'),
        ),
    ]
