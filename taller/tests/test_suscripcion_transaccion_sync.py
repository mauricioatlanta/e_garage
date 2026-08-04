import shutil
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.utils import timezone

from taller.models.comprobante_pago import ComprobantePago
from taller.models.empresa import Empresa
from taller.models.pago import PagoPendiente
from taller.models.suscripcion_transaccion import SuscripcionTransaccion


User = get_user_model()


@pytest.fixture(autouse=True)
def _sync_test_settings(settings):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.MEDIA_ROOT = "C:/Users/Mauricio/.codex/memories/tmp_test_media_sync"
    target = Path(settings.MEDIA_ROOT)
    shutil.rmtree(target, ignore_errors=True)
    target.mkdir(parents=True, exist_ok=True)
    yield
    shutil.rmtree(target, ignore_errors=True)


def _empresa(username="sync-user", email="sync@example.com", pais="CL"):
    from taller.tests.factories import EmpresaFactory
    return EmpresaFactory(
        nombre_taller=f"Taller {username}",
        email=email,
        telefono="+56911112222",
        pais=pais,
        plan="trial",
        suscripcion_activa=False,
        fecha_inicio=timezone.now() - timedelta(days=35),
        fecha_fin=timezone.now() - timedelta(days=1),
        valor_mensual=Decimal("0.00"),
    )


@pytest.mark.django_db
def test_pago_pendiente_sync_creates_unified_transaction(monkeypatch):
    monkeypatch.setattr(
        "taller.utils.notificaciones_suscripcion.notificar_nueva_suscripcion",
        lambda **kwargs: None,
    )

    empresa = _empresa(username="sync-pago", email="sync-pago@example.com")
    pago = PagoPendiente.objects.create(
        empresa=empresa,
        plan="mensual",
        monto=Decimal("10000.00"),
        comprobante=SimpleUploadedFile("voucher.pdf", b"voucher", content_type="application/pdf"),
        referencia="PAY-001",
        metodo_pago="transferencia",
        estado="pendiente",
    )

    tx = SuscripcionTransaccion.objects.get(legacy_pago_pendiente=pago)

    assert tx.source_type == "legacy_pago_pendiente"
    assert tx.status == "pending"
    assert tx.payment_method == "transferencia"
    assert tx.billing_cycle == "mensual"
    assert tx.plan_code == "basic"
    assert tx.reference == "PAY-001"


@pytest.mark.django_db
def test_comprobante_pago_sync_updates_unified_transaction(monkeypatch):
    monkeypatch.setattr(
        "taller.models.comprobante_pago.ComprobantePago.enviar_notificacion_admin",
        lambda self: None,
    )
    monkeypatch.setattr(
        "taller.models.comprobante_pago.ComprobantePago.enviar_notificacion_rechazo",
        lambda self: None,
    )

    empresa = _empresa(username="sync-comp", email="sync-comp@example.com")
    comprobante = ComprobantePago.objects.create(
        empresa=empresa,
        metodo_pago="mercadopago",
        monto=Decimal("55000.00"),
        moneda="CLP",
        comprobante=SimpleUploadedFile("voucher.png", b"img", content_type="image/png"),
        numero_transaccion="MP-001",
        descripcion="Pago de prueba",
        plan_solicitado="premium",
        meses_pagados=6,
    )

    tx = SuscripcionTransaccion.objects.get(legacy_comprobante_pago=comprobante)
    assert tx.status == "pending"
    assert tx.payment_method == "mercadopago"
    assert tx.billing_cycle == "semestral"
    assert tx.plan_code == "premium"

    comprobante.rechazar("Datos incompletos", procesado_por="admin-test")
    tx.refresh_from_db()

    assert tx.status == "rejected"
    assert tx.processed_by == "admin-test"
    assert tx.admin_notes == "Datos incompletos"


@pytest.mark.django_db
def test_backfill_command_is_idempotent(monkeypatch):
    monkeypatch.setattr(
        "taller.models.comprobante_pago.ComprobantePago.enviar_notificacion_admin",
        lambda self: None,
    )

    empresa = _empresa(username="sync-backfill", email="sync-backfill@example.com")
    PagoPendiente.objects.create(
        empresa=empresa,
        plan="anual",
        monto=Decimal("100000.00"),
        comprobante=SimpleUploadedFile("voucher.pdf", b"voucher", content_type="application/pdf"),
        referencia="PAY-ANUAL-1",
        metodo_pago="transferencia",
        estado="pendiente",
    )
    ComprobantePago.objects.create(
        empresa=empresa,
        metodo_pago="paypal",
        monto=Decimal("200.00"),
        moneda="USD",
        comprobante=SimpleUploadedFile("voucher.png", b"img", content_type="image/png"),
        numero_transaccion="PP-001",
        plan_solicitado="enterprise",
        meses_pagados=12,
    )

    initial_count = SuscripcionTransaccion.objects.count()
    call_command("backfill_suscripcion_transacciones")
    call_command("backfill_suscripcion_transacciones")

    assert SuscripcionTransaccion.objects.count() == initial_count
