# Generated by Django 5.2.1 on 2025-06-29 17:49

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('listings', '0003_alter_payment_payment_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='payment_id',
            field=models.UUIDField(default=uuid.UUID('49b17cde-148f-47b8-ba4a-e28a9d0c242f'), editable=False, primary_key=True, serialize=False),
        ),
    ]
