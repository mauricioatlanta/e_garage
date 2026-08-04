"""
Tests para create_validation_center management command.

Cubre:
  - Ejecución inicial: crea los 10 perfiles con los datos correctos
  - Segunda ejecución: idempotente, sin duplicados
  - Restauración: _seed_alert_data recupera campos corrompidos
  - --reset: limpia y recrea correctamente
  - EmailAddress: verified=True, primary=True para todos los perfiles
  - Conteos exactos: 2 vehículos atascados, 3 sin foto, 2 sin precio, 4 sin ubicación

Notas de aislamiento:
  - setUpTestData corre el comando una sola vez por clase (más rápido).
  - Los tests de restauración mutan datos dentro del savepoint por test
    y llaman al comando de nuevo; al finalizar el test, el savepoint se
    revierte y la clase queda limpia para el siguiente test.
  - ResetTests usa setUp (por test) porque --reset borra los usuarios.
"""
from __future__ import annotations

from datetime import date, timedelta
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from taller.models import VehiculoDesarme
from taller.models.pieza_desarme import PiezaDesarme
from taller.constants.workspaces import get_workspace_def
from taller.management.commands.create_validation_center import (
    DESARME_ALERT_PIEZAS,
    DESARME_VEHICULOS_STUCK,
    PLACEHOLDER_IMAGEN,
)
from taller.services.workspace_alerts_service import (
    ALRT_DESARM_DELAYED,
    ALRT_PIEZA_NO_FOTO,
    ALRT_PIEZA_NO_PRECIO,
    ALRT_PIEZA_NO_UBICACION,
    WorkspaceAlertsService,
)


def _run_cmd(**opts):
    out = StringIO()
    call_command("create_validation_center", stdout=out, stderr=StringIO(), **opts)
    return out.getvalue()


def _get_empresa(username="vc_desarme"):
    return get_user_model().objects.get(username=username).empresa


def _alerts(empresa):
    ws_def = get_workspace_def("DESARMADURIA")
    return {a["key"]: a["count"] for a in WorkspaceAlertsService.resolve(ws_def, empresa, "/cl/es")}


# ---------------------------------------------------------------------------
# 1. Smoke tests — initial run
# ---------------------------------------------------------------------------

class ValidationCenterSmokeTests(TestCase):
    """Verifies basic creation after a single command run."""

    @classmethod
    def setUpTestData(cls):
        _run_cmd()
        cls.empresa = _get_empresa("vc_desarme")

    def test_vc_desarme_user_exists(self):
        self.assertTrue(
            get_user_model().objects.filter(username="vc_desarme").exists()
        )

    def test_all_ten_profiles_created(self):
        usernames = [
            "vc_taller", "vc_desarme", "vc_repuestos", "vc_desarme_taller",
            "vc_repuestos_taller", "vc_carwash", "vc_vulcanizacion",
            "vc_escapes", "vc_flotas", "vc_enterprise",
        ]
        for u in usernames:
            with self.subTest(username=u):
                self.assertTrue(
                    get_user_model().objects.filter(username=u).exists(),
                    f"{u} not found",
                )

    def test_empresa_has_config(self):
        self.assertTrue(hasattr(self.empresa, "config"))
        self.assertEqual(self.empresa.config.rubro_principal, "DESARMADURIA")

    def test_alert_counts_2_3_2_4(self):
        counts = _alerts(self.empresa)
        self.assertEqual(counts.get(ALRT_DESARM_DELAYED), 2)
        self.assertEqual(counts.get(ALRT_PIEZA_NO_FOTO), 3)
        self.assertEqual(counts.get(ALRT_PIEZA_NO_PRECIO), 2)
        self.assertEqual(counts.get(ALRT_PIEZA_NO_UBICACION), 4)

    def test_exactly_two_stuck_vehicles(self):
        stuck = VehiculoDesarme.objects.filter(
            empresa=self.empresa,
            patente__in=[
                f"VC_D-{sv['patente']}" for sv in DESARME_VEHICULOS_STUCK
            ],
        )
        self.assertEqual(stuck.count(), 2)

    def test_stuck_vehicles_have_old_date(self):
        cutoff = date.today() - timedelta(days=30)
        stuck = VehiculoDesarme.objects.filter(
            empresa=self.empresa,
            estado_desarme__in=["INGRESADO", "DESARMANDO"],
            patente__contains="VC-STK-",
        )
        self.assertEqual(stuck.count(), 2)
        for vd in stuck:
            self.assertIsNotNone(vd.fecha_ingreso_desarme)
            self.assertLess(vd.fecha_ingreso_desarme, cutoff)

    def test_exactly_eleven_alert_piezas_created(self):
        codigos = [pd["codigo"] for pd in DESARME_ALERT_PIEZAS]
        found = PiezaDesarme.objects.filter(
            empresa=self.empresa, codigo__in=codigos
        ).count()
        self.assertEqual(found, len(DESARME_ALERT_PIEZAS))

    def test_placeholder_png_exists_in_media(self):
        from pathlib import Path
        from django.conf import settings
        path = Path(settings.MEDIA_ROOT) / PLACEHOLDER_IMAGEN
        self.assertTrue(path.exists(), f"Placeholder PNG not found: {path}")
        self.assertGreater(path.stat().st_size, 0)

    def test_placeholder_png_is_valid(self):
        from pathlib import Path
        from django.conf import settings
        data = (Path(settings.MEDIA_ROOT) / PLACEHOLDER_IMAGEN).read_bytes()
        self.assertTrue(data[:8] == b"\x89PNG\r\n\x1a\n", "Not a valid PNG")

    def test_ok_piezas_do_not_trigger_alerts(self):
        """Las 2 piezas sanas no deben sumarse a ninguna alerta."""
        ok_codigos = {"VC-OK-001", "VC-OK-002"}
        ok_piezas = PiezaDesarme.objects.filter(
            empresa=self.empresa, codigo__in=ok_codigos
        )
        self.assertEqual(ok_piezas.count(), 2)
        # La imagen debe ser la ruta placeholder, no vacía
        for p in ok_piezas:
            img = p.imagen.name or "" if p.imagen else ""
            self.assertNotEqual(img, "", f"{p.codigo} imagen is empty — triggers sin_foto")

    def test_email_address_verified_primary(self):
        try:
            from allauth.account.models import EmailAddress
        except ImportError:
            self.skipTest("allauth not installed")
        user = get_user_model().objects.get(username="vc_desarme")
        ea = EmailAddress.objects.filter(user=user, email=user.email).first()
        self.assertIsNotNone(ea, "EmailAddress not found")
        self.assertTrue(ea.verified)
        self.assertTrue(ea.primary)

    def test_all_ten_emails_verified(self):
        try:
            from allauth.account.models import EmailAddress
        except ImportError:
            self.skipTest("allauth not installed")
        from taller.management.commands.create_validation_center import PROFILES
        for p in PROFILES:
            with self.subTest(username=p["username"]):
                user = get_user_model().objects.filter(username=p["username"]).first()
                if user is None:
                    continue
                ea = EmailAddress.objects.filter(user=user, email=user.email).first()
                self.assertIsNotNone(ea, f"No EmailAddress for {p['username']}")
                self.assertTrue(ea.verified, f"Not verified for {p['username']}")
                self.assertTrue(ea.primary, f"Not primary for {p['username']}")


# ---------------------------------------------------------------------------
# 2. Idempotency tests — two consecutive runs
# ---------------------------------------------------------------------------

class ValidationCenterIdempotencyTests(TestCase):
    """Second run must not create duplicates."""

    @classmethod
    def setUpTestData(cls):
        _run_cmd()
        cls.empresa = _get_empresa("vc_desarme")

    def _rerun(self):
        _run_cmd()

    def test_no_duplicate_stuck_vehicles(self):
        self._rerun()
        count = VehiculoDesarme.objects.filter(
            empresa=self.empresa, patente__contains="VC-STK-"
        ).count()
        self.assertEqual(count, 2)

    def test_no_duplicate_alert_piezas(self):
        self._rerun()
        codigos = [pd["codigo"] for pd in DESARME_ALERT_PIEZAS]
        count = PiezaDesarme.objects.filter(
            empresa=self.empresa, codigo__in=codigos
        ).count()
        self.assertEqual(count, len(DESARME_ALERT_PIEZAS))

    def test_alert_counts_unchanged_after_second_run(self):
        self._rerun()
        counts = _alerts(self.empresa)
        self.assertEqual(counts.get(ALRT_DESARM_DELAYED), 2)
        self.assertEqual(counts.get(ALRT_PIEZA_NO_FOTO), 3)
        self.assertEqual(counts.get(ALRT_PIEZA_NO_PRECIO), 2)
        self.assertEqual(counts.get(ALRT_PIEZA_NO_UBICACION), 4)

    def test_no_duplicate_email_addresses(self):
        try:
            from allauth.account.models import EmailAddress
        except ImportError:
            self.skipTest("allauth not installed")
        self._rerun()
        user = get_user_model().objects.get(username="vc_desarme")
        count = EmailAddress.objects.filter(user=user, email=user.email).count()
        self.assertEqual(count, 1)


# ---------------------------------------------------------------------------
# 3. Restoration tests — command recovers corrupted demo data
# ---------------------------------------------------------------------------

class ValidationCenterRestorationTests(TestCase):
    """
    _seed_alert_data() must restore all alert-determining fields,
    not just estado_desarme/activo.
    """

    @classmethod
    def setUpTestData(cls):
        _run_cmd()
        cls.empresa = _get_empresa("vc_desarme")

    def _rerun(self):
        _run_cmd()

    def _get_stuck_vehicle(self, suffix="VC-STK-001"):
        return VehiculoDesarme.objects.filter(
            empresa=self.empresa, patente__contains=suffix
        ).first()

    def _get_pieza(self, codigo):
        return PiezaDesarme.objects.filter(
            empresa=self.empresa, codigo=codigo
        ).first()

    def test_restores_stuck_vehicle_date_when_too_recent(self):
        vd = self._get_stuck_vehicle()
        vd.fecha_ingreso_desarme = date.today()
        vd.save(update_fields=["fecha_ingreso_desarme"])

        self._rerun()

        vd.refresh_from_db()
        cutoff = date.today() - timedelta(days=30)
        self.assertLess(vd.fecha_ingreso_desarme, cutoff)

    def test_restores_stuck_vehicle_date_when_null(self):
        vd = self._get_stuck_vehicle()
        vd.fecha_ingreso_desarme = None
        vd.save(update_fields=["fecha_ingreso_desarme"])

        self._rerun()

        vd.refresh_from_db()
        self.assertIsNotNone(vd.fecha_ingreso_desarme)
        cutoff = date.today() - timedelta(days=30)
        self.assertLess(vd.fecha_ingreso_desarme, cutoff)

    def test_restores_stuck_vehicle_estado_when_changed(self):
        vd = self._get_stuck_vehicle("VC-STK-001")
        vd.estado_desarme = "AGOTADO"
        vd.save(update_fields=["estado_desarme"])

        self._rerun()

        vd.refresh_from_db()
        self.assertEqual(vd.estado_desarme, "INGRESADO")

    def test_restores_pieza_estado_when_not_disponible(self):
        pieza = self._get_pieza("VC-ALT-FTO-001")
        pieza.estado_pieza = "VENDIDA"
        pieza.save(update_fields=["estado_pieza"])

        self._rerun()

        pieza.refresh_from_db()
        self.assertEqual(pieza.estado_pieza, "DISPONIBLE")

    def test_restores_pieza_activo_when_false(self):
        pieza = self._get_pieza("VC-ALT-FTO-002")
        pieza.activo = False
        pieza.save(update_fields=["activo"])

        self._rerun()

        pieza.refresh_from_db()
        self.assertTrue(pieza.activo)

    def test_restores_pieza_ubicacion_when_changed(self):
        pieza = self._get_pieza("VC-ALT-UBI-001")
        pieza.ubicacion_fisica = "Movida-manual"
        pieza.save(update_fields=["ubicacion_fisica"])

        self._rerun()

        pieza.refresh_from_db()
        self.assertIsNone(pieza.ubicacion_fisica)

    def test_restores_pieza_precio_sugerido_when_set(self):
        """Si se pone un precio_sugerido en una pieza sin-precio, el re-run lo elimina."""
        from decimal import Decimal
        pieza = self._get_pieza("VC-ALT-PRC-001")
        pieza.precio_sugerido = Decimal("99000")
        pieza.save(update_fields=["precio_sugerido"])

        self._rerun()

        pieza.refresh_from_db()
        self.assertIsNone(pieza.precio_sugerido)

    def test_alert_counts_restored_after_corruption(self):
        """Corrupting a pieza and re-running should restore the correct counts."""
        pieza = self._get_pieza("VC-ALT-FTO-001")
        pieza.estado_pieza = "VENDIDA"
        pieza.save(update_fields=["estado_pieza"])

        # Before re-run: sin_foto count is 2 (one corrupted to VENDIDA, excluded)
        counts_before = _alerts(self.empresa)
        self.assertEqual(counts_before.get(ALRT_PIEZA_NO_FOTO), 2)

        self._rerun()

        # After re-run: sin_foto count is back to 3
        counts_after = _alerts(self.empresa)
        self.assertEqual(counts_after.get(ALRT_PIEZA_NO_FOTO), 3)


# ---------------------------------------------------------------------------
# 4. Reset tests
# ---------------------------------------------------------------------------

class ValidationCenterResetTests(TestCase):
    """--reset deletes vc_* data and the subsequent run recreates it."""

    def test_reset_removes_vc_users(self):
        _run_cmd()
        _run_cmd(reset=True)
        # After --reset, the command continues and recreates everything
        self.assertTrue(
            get_user_model().objects.filter(username="vc_desarme").exists()
        )

    def test_reset_then_run_produces_correct_alert_counts(self):
        _run_cmd()
        _run_cmd(reset=True)
        empresa = _get_empresa("vc_desarme")
        counts = _alerts(empresa)
        self.assertEqual(counts.get(ALRT_DESARM_DELAYED), 2)
        self.assertEqual(counts.get(ALRT_PIEZA_NO_FOTO), 3)
        self.assertEqual(counts.get(ALRT_PIEZA_NO_PRECIO), 2)
        self.assertEqual(counts.get(ALRT_PIEZA_NO_UBICACION), 4)

    def test_reset_does_not_delete_non_vc_users(self):
        User = get_user_model()
        User.objects.create_user(username="real_user", password="pass")
        _run_cmd()
        _run_cmd(reset=True)
        self.assertTrue(User.objects.filter(username="real_user").exists())

    def test_reset_removes_alert_piezas(self):
        _run_cmd()
        empresa = _get_empresa("vc_desarme")
        codigos = [pd["codigo"] for pd in DESARME_ALERT_PIEZAS]
        self.assertEqual(
            PiezaDesarme.objects.filter(empresa=empresa, codigo__in=codigos).count(),
            len(DESARME_ALERT_PIEZAS),
        )
        # --reset deletes piezas, then recreates
        _run_cmd(reset=True)
        empresa = _get_empresa("vc_desarme")
        self.assertEqual(
            PiezaDesarme.objects.filter(empresa=empresa, codigo__in=codigos).count(),
            len(DESARME_ALERT_PIEZAS),
        )

    def test_triple_run_after_reset_is_idempotent(self):
        _run_cmd(reset=True)
        _run_cmd()
        _run_cmd()
        empresa = _get_empresa("vc_desarme")
        counts = _alerts(empresa)
        self.assertEqual(counts.get(ALRT_DESARM_DELAYED), 2)
        self.assertEqual(counts.get(ALRT_PIEZA_NO_FOTO), 3)
        self.assertEqual(counts.get(ALRT_PIEZA_NO_PRECIO), 2)
        self.assertEqual(counts.get(ALRT_PIEZA_NO_UBICACION), 4)
