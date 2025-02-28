# Generated by Django 4.2.13 on 2024-07-30 22:39

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("core", "0002_savingsgoal_expense"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="email_notifications",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="profile",
            name="low_balance_threshold",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name="profile",
            name="sms_notifications",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="transaction",
            name="transaction_type",
            field=models.CharField(
                choices=[
                    ("DEPOSIT", "Deposit"),
                    ("WITHDRAWAL", "Withdrawal"),
                    ("TRANSFER", "Transfer"),
                    ("PAYMENT", "Payment"),
                ],
                max_length=20,
            ),
        ),
        migrations.CreateModel(
            name="Notification",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("message", models.TextField()),
                ("timestamp", models.DateTimeField(auto_now_add=True)),
                ("sent_via_email", models.BooleanField(default=False)),
                ("sent_via_sms", models.BooleanField(default=False)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
