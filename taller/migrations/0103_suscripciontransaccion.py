import uuid

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("taller", "0102_documento_public_approval_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="SuscripcionTransaccion",
            fields=[
                (
                    "id",
                    models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID"),
                ),
                ("uuid", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                (
                    "source_type",
                    models.CharField(
                        choices=[
                            ("legacy_pago_pendiente", "Legacy PagoPendiente"),
                            ("legacy_comprobante_pago", "Legacy ComprobantePago"),
                            ("flow", "Flow"),
                            ("mercadopago", "MercadoPago"),
                            ("paypal", "PayPal"),
                            ("transferencia_manual", "Transferencia Manual"),
                            ("otro", "Otro"),
                        ],
                        db_index=True,
                        max_length=40,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pendiente"),
                            ("processing", "En proceso"),
                            ("approved", "Aprobada"),
                            ("rejected", "Rechazada"),
                            ("cancelled", "Cancelada"),
                            ("error", "Error"),
                        ],
                        db_index=True,
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("raw_status", models.CharField(blank=True, max_length=50)),
                (
                    "payment_method",
                    models.CharField(
                        choices=[
                            ("transferencia", "Transferencia Bancaria"),
                            ("flow", "Flow"),
                            ("webpay", "WebPay Plus"),
                            ("khipu", "Khipu"),
                            ("mercadopago", "MercadoPago"),
                            ("paypal", "PayPal"),
                            ("otro", "Otro"),
                        ],
                        default="transferencia",
                        max_length=30,
                    ),
                ),
                (
                    "billing_cycle",
                    models.CharField(
                        choices=[
                            ("mensual", "Mensual"),
                            ("semestral", "Semestral"),
                            ("anual", "Anual"),
                            ("otro", "Otro"),
                        ],
                        default="mensual",
                        max_length=20,
                    ),
                ),
                (
                    "plan_code",
                    models.CharField(
                        choices=[
                            ("trial", "Prueba Gratuita"),
                            ("basic", "Plan Básico"),
                            ("premium", "Plan Premium"),
                            ("enterprise", "Plan Empresarial"),
                        ],
                        default="basic",
                        max_length=20,
                    ),
                ),
                ("months_paid", models.PositiveIntegerField(default=1)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=12)),
                ("currency", models.CharField(default="CLP", max_length=3)),
                ("reference", models.CharField(blank=True, db_index=True, max_length=120)),
                ("external_transaction_id", models.CharField(blank=True, db_index=True, max_length=120)),
                ("checkout_url", models.URLField(blank=True)),
                ("customer_email", models.EmailField(blank=True, max_length=254)),
                ("receipt_path", models.CharField(blank=True, max_length=500)),
                ("description", models.TextField(blank=True)),
                ("admin_notes", models.TextField(blank=True)),
                ("gateway_payload", models.JSONField(blank=True, default=dict)),
                ("submitted_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ("processed_at", models.DateTimeField(blank=True, null=True)),
                ("subscription_applied_at", models.DateTimeField(blank=True, null=True)),
                ("processed_by", models.CharField(blank=True, max_length=150)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "empresa",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="suscripcion_transacciones",
                        to="taller.empresa",
                    ),
                ),
                (
                    "legacy_comprobante_pago",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="suscripcion_transaccion",
                        to="taller.comprobantepago",
                    ),
                ),
                (
                    "legacy_pago_pendiente",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="suscripcion_transaccion",
                        to="taller.pagopendiente",
                    ),
                ),
            ],
            options={
                "verbose_name": "Transacción de Suscripción",
                "verbose_name_plural": "Transacciones de Suscripción",
                "ordering": ["-submitted_at", "-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="suscripciontransaccion",
            index=models.Index(fields=["empresa", "status"], name="t_susc_emp_b56f73_idx"),
        ),
        migrations.AddIndex(
            model_name="suscripciontransaccion",
            index=models.Index(fields=["payment_method", "status"], name="t_susc_pay_461adc_idx"),
        ),
        migrations.AddIndex(
            model_name="suscripciontransaccion",
            index=models.Index(fields=["source_type", "submitted_at"], name="t_susc_src_e43df4_idx"),
        ),
    ]
