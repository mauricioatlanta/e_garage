# Generated manually for subscription plan changes.

import decimal
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("taller", "0112_alter_comprobantepago_plan_solicitado_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="SubscriptionChange",
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
                (
                    "current_plan",
                    models.CharField(
                        choices=[
                            ("trial", "Trial"),
                            ("entry", "Entry"),
                            ("growth", "Growth"),
                            ("business", "Business"),
                            ("basic", "Plan Básico"),
                            ("premium", "Plan Premium"),
                            ("enterprise", "Plan Empresarial"),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    "requested_plan",
                    models.CharField(
                        choices=[
                            ("trial", "Trial"),
                            ("entry", "Entry"),
                            ("growth", "Growth"),
                            ("business", "Business"),
                            ("basic", "Plan Básico"),
                            ("premium", "Plan Premium"),
                            ("enterprise", "Plan Empresarial"),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    "change_type",
                    models.CharField(
                        choices=[("upgrade", "Upgrade"), ("downgrade", "Downgrade")],
                        max_length=20,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pendiente"),
                            ("scheduled", "Programado"),
                            ("completed", "Completado"),
                            ("cancelled", "Cancelado"),
                            ("failed", "Fallido"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("billing_cycle", models.CharField(default="monthly", max_length=20)),
                (
                    "prorated_amount",
                    models.DecimalField(
                        decimal_places=2,
                        default=decimal.Decimal("0.00"),
                        max_digits=12,
                    ),
                ),
                ("currency", models.CharField(default="USD", max_length=3)),
                ("scheduled_at", models.DateTimeField(blank=True, db_index=True, null=True)),
                ("applied_at", models.DateTimeField(blank=True, null=True)),
                ("cancelled_at", models.DateTimeField(blank=True, null=True)),
                ("failure_reason", models.TextField(blank=True)),
                ("validation_snapshot", models.JSONField(blank=True, default=dict)),
                (
                    "created_at",
                    models.DateTimeField(db_index=True, default=django.utils.timezone.now),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "empresa",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="subscription_changes",
                        to="taller.empresa",
                    ),
                ),
                (
                    "requested_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="requested_subscription_changes",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "transaction",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="subscription_changes",
                        to="taller.suscripciontransaccion",
                    ),
                ),
            ],
            options={
                "verbose_name": "Cambio de Suscripción",
                "verbose_name_plural": "Cambios de Suscripción",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="subscriptionchange",
            index=models.Index(fields=["empresa", "status"], name="taller_subs_empresa_76b9f4_idx"),
        ),
        migrations.AddIndex(
            model_name="subscriptionchange",
            index=models.Index(
                fields=["change_type", "status", "scheduled_at"],
                name="taller_subs_change__3cf7f2_idx",
            ),
        ),
        migrations.AddConstraint(
            model_name="subscriptionchange",
            constraint=models.UniqueConstraint(
                condition=models.Q(("status__in", ["pending", "scheduled"])),
                fields=("empresa",),
                name="uniq_open_subscription_change_per_empresa",
            ),
        ),
    ]
