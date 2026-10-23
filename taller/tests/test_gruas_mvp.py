from decimal import Decimal
from datetime import timedelta
from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import Http404
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory
from django.test import TestCase
from django.utils import timezone

from taller.gruas.permissions import ensure_order_access
from taller.gruas.forms import TowingEvidenceForm
from taller.gruas import views as gruas_views
from taller.gruas.services.assignment_service import assign_order
from taller.gruas.services.financial_service import add_entry, financial_summary
from taller.gruas.services.order_service import accept_quote, create_quote, transition_order
from taller.models import Cliente, Documento, Empresa, TowingDriver, TowingEvidence, TowingLedgerEntry, TowingOrder, TowingUnit


class TowingMVPTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user("tow-owner", password="x")
        self.other = User.objects.create_user("tow-other", password="x")
        self.empresa = Empresa.objects.create(user=self.owner, nombre_taller="Grúas Test", pais="CL", moneda="CLP")
        self.other_empresa = Empresa.objects.create(user=self.other, nombre_taller="Otra", pais="CL", moneda="CLP")
        self.unit = TowingUnit.objects.create(empresa=self.empresa, nombre="Plataforma 1", patente="ABC-123", estado="ACTIVA")
        self.driver_user = User.objects.create_user("driver", password="x")
        self.driver = TowingDriver.objects.create(empresa=self.empresa, user=self.driver_user, nombre="Conductor")
        self.order = TowingOrder.objects.create(empresa=self.empresa, numero="GR-000001", origen="A", destino="B", patente_snapshot="AA11")

    def test_quote_acceptance_keeps_history_and_one_current(self):
        first = create_quote(order_id=self.order.id, empresa=self.empresa, user=self.owner, net_amount=Decimal("10000"), tax_rate=Decimal("19"))
        accept_quote(quote_id=first.id, empresa=self.empresa, user=self.owner)
        second = create_quote(order_id=self.order.id, empresa=self.empresa, user=self.owner, net_amount=Decimal("15000"), tax_rate=Decimal("19"))
        accept_quote(quote_id=second.id, empresa=self.empresa, user=self.owner)
        self.assertEqual(self.order.quotes.count(), 2)
        self.assertEqual(self.order.quotes.filter(is_current=True).count(), 1)
        self.assertFalse(self.order.quotes.get(pk=first.id).is_current)

    def test_assignment_rejects_overlapping_resource(self):
        quote = create_quote(order_id=self.order.id, empresa=self.empresa, user=self.owner, net_amount=Decimal("100"), tax_rate=Decimal("0"))
        accept_quote(quote_id=quote.id, empresa=self.empresa, user=self.owner)
        start = timezone.now() + timedelta(hours=1)
        end = start + timedelta(hours=2)
        assign_order(order_id=self.order.id, empresa=self.empresa, unit_id=self.unit.id, driver_id=self.driver.id, planned_start_at=start, planned_end_at=end, user=self.owner)
        second = TowingOrder.objects.create(empresa=self.empresa, numero="GR-000002", origen="C", destino="D")
        with self.assertRaises(ValidationError):
            assign_order(order_id=second.id, empresa=self.empresa, unit_id=self.unit.id, driver_id=self.driver.id, planned_start_at=start + timedelta(minutes=30), planned_end_at=end + timedelta(hours=1), user=self.owner)

    def test_financial_summary_uses_net_collections_and_expenses(self):
        quote = create_quote(order_id=self.order.id, empresa=self.empresa, user=self.owner, net_amount=Decimal("10000"), tax_rate=Decimal("0"))
        accept_quote(quote_id=quote.id, empresa=self.empresa, user=self.owner)
        add_entry(order_id=self.order.id, empresa=self.empresa, entry_type="ADVANCE", amount=Decimal("5000"), currency="CLP", user=self.owner)
        add_entry(order_id=self.order.id, empresa=self.empresa, entry_type="REFUND", amount=Decimal("1000"), currency="CLP", user=self.owner)
        add_entry(order_id=self.order.id, empresa=self.empresa, entry_type="EXPENSE", amount=Decimal("2000"), currency="CLP", user=self.owner)
        summary = financial_summary(self.order)
        self.assertEqual(summary["net_collected"], Decimal("4000"))
        self.assertEqual(summary["balance"], Decimal("6000"))
        self.assertEqual(summary["recorded_margin"], Decimal("8000"))

    def test_charge_is_not_cash_and_reversal_rules_are_explicit(self):
        quote = create_quote(order_id=self.order.id, empresa=self.empresa, user=self.owner, net_amount=Decimal("10000"), tax_rate=Decimal("0"))
        accept_quote(quote_id=quote.id, empresa=self.empresa, user=self.owner)
        charge = add_entry(order_id=self.order.id, empresa=self.empresa, entry_type=TowingLedgerEntry.CHARGE, amount=Decimal("10000"), currency="CLP", user=self.owner)
        self.assertEqual(financial_summary(self.order)["net_collected"], Decimal("0"))
        with self.assertRaises(ValidationError):
            add_entry(order_id=self.order.id, empresa=self.empresa, entry_type=TowingLedgerEntry.EXPENSE_REVERSAL, amount=Decimal("1"), currency="CLP", user=self.owner, reversed_entry=charge)

    def test_document_link_does_not_duplicate_order_finance(self):
        cliente = Cliente.objects.create(empresa=self.empresa, nombre="Pagador")
        documento = Documento.objects.create(empresa=self.empresa, cliente=cliente, tipo="PRES", total=Decimal("10000"))
        self.order.documento = documento
        self.order.save(update_fields=["documento"])
        quote = create_quote(order_id=self.order.id, empresa=self.empresa, user=self.owner, net_amount=Decimal("10000"), tax_rate=Decimal("0"))
        accept_quote(quote_id=quote.id, empresa=self.empresa, user=self.owner)
        add_entry(order_id=self.order.id, empresa=self.empresa, entry_type=TowingLedgerEntry.PAYMENT, amount=Decimal("2500"), currency="CLP", user=self.owner)
        self.assertEqual(financial_summary(self.order)["net_collected"], Decimal("2500"))

    def test_evidence_storage_has_no_public_media_url(self):
        evidence = TowingEvidence(order=self.order, kind="RETIRO", created_by=self.owner)
        evidence.file.save("proof.txt", SimpleUploadedFile("proof.txt", b"private"), save=False)
        with self.assertRaises(ValueError):
            evidence.file.url
        evidence.file.delete(save=False)

    def test_driver_cannot_access_other_company_order(self):
        foreign = TowingOrder.objects.create(empresa=self.other_empresa, numero="GR-000001", origen="X", destino="Y")
        request = SimpleNamespace(user=self.driver_user, empresa=self.empresa)
        with self.assertRaises(PermissionDenied):
            ensure_order_access(request, foreign, driver_only=True)

    def test_close_is_independent_of_payment(self):
        quote = create_quote(order_id=self.order.id, empresa=self.empresa, user=self.owner, net_amount=Decimal("100"), tax_rate=Decimal("0"))
        accept_quote(quote_id=quote.id, empresa=self.empresa, user=self.owner)
        for status in (TowingOrder.STATUS_ASSIGNED, TowingOrder.STATUS_EN_ROUTE, TowingOrder.STATUS_PICKUP, TowingOrder.STATUS_LOADED, TowingOrder.STATUS_TRANSIT, TowingOrder.STATUS_DELIVERED, TowingOrder.STATUS_CLOSED):
            if status == TowingOrder.STATUS_ASSIGNED:
                self.order.status = TowingOrder.STATUS_ACCEPTED
                self.order.save(update_fields=["status"])
            transition_order(order_id=self.order.id, empresa=self.empresa, to_status=status, user=self.owner)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, TowingOrder.STATUS_CLOSED)
        self.assertEqual(financial_summary(self.order)["balance"], Decimal("100"))

    def test_complete_transfer_from_quote_to_delivery_and_balance(self):
        """Smoke test for the dispatcher/driver vertical, including evidence."""
        quote = create_quote(
            order_id=self.order.id, empresa=self.empresa, user=self.owner,
            net_amount=Decimal("70000"), tax_rate=Decimal("0"), included_km=Decimal("25"),
        )
        accept_quote(quote_id=quote.id, empresa=self.empresa, user=self.owner)
        start = timezone.now() + timedelta(hours=1)
        assignment = assign_order(
            order_id=self.order.id, empresa=self.empresa, user=self.owner,
            unit_id=self.unit.id, driver_id=self.driver.id,
            planned_start_at=start, planned_end_at=start + timedelta(hours=2),
        )

        for status in (
            TowingOrder.STATUS_EN_ROUTE, TowingOrder.STATUS_PICKUP,
            TowingOrder.STATUS_LOADED, TowingOrder.STATUS_TRANSIT,
            TowingOrder.STATUS_DELIVERED,
        ):
            transition_order(order_id=self.order.id, empresa=self.empresa, to_status=status, user=self.driver_user)

        evidence = TowingEvidence(
            order=self.order, assignment=assignment, kind="RETIRO",
            created_by=self.driver_user,
        )
        evidence.file.save("retiro.txt", SimpleUploadedFile("retiro.txt", b"foto de prueba"), save=True)
        add_entry(order_id=self.order.id, empresa=self.empresa, entry_type=TowingLedgerEntry.EXPENSE, amount=Decimal("12000"), currency="CLP", user=self.owner, reference="combustible")
        add_entry(order_id=self.order.id, empresa=self.empresa, entry_type=TowingLedgerEntry.ADVANCE, amount=Decimal("30000"), currency="CLP", user=self.owner, reference="abono")
        transition_order(order_id=self.order.id, empresa=self.empresa, to_status=TowingOrder.STATUS_CLOSED, user=self.owner)

        self.order.refresh_from_db()
        summary = financial_summary(self.order)
        self.assertEqual(self.order.status, TowingOrder.STATUS_CLOSED)
        self.assertEqual(self.order.evidences.count(), 1)
        self.assertEqual(summary["accepted_total"], Decimal("70000.00"))
        self.assertEqual(summary["net_collected"], Decimal("30000.00"))
        self.assertEqual(summary["balance"], Decimal("40000.00"))
        self.assertEqual(summary["recorded_margin"], Decimal("58000.00"))
        evidence.file.delete(save=False)

    def test_assigned_driver_can_upload_and_download_photo_only_for_active_order(self):
        quote = create_quote(order_id=self.order.id, empresa=self.empresa, user=self.owner, net_amount=Decimal("1000"), tax_rate=Decimal("0"))
        accept_quote(quote_id=quote.id, empresa=self.empresa, user=self.owner)
        start = timezone.now() + timedelta(hours=1)
        assignment = assign_order(
            order_id=self.order.id, empresa=self.empresa, user=self.owner,
            unit_id=self.unit.id, driver_id=self.driver.id,
            planned_start_at=start, planned_end_at=start + timedelta(hours=1),
        )
        png = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0dIDAT"
            b"x\x9cc\xf8\xcf\xc0\xf0\x1f\x00\x05\x00\x01\xff\x89\x99=\x1d\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        request = RequestFactory().post(
            f"/cl/es/gruas/conductor/ordenes/{self.order.id}/evidencias/",
            {"kind": "RETIRO", "description": "Foto de prueba", "file": SimpleUploadedFile("retiro.png", png, content_type="image/png")},
            HTTP_HOST="testserver",
        )
        request.user = self.driver_user
        request.empresa = self.empresa
        request.session = {}
        request._messages = FallbackStorage(request)
        response = gruas_views.driver_evidence_upload.__wrapped__(request, self.order.id)
        self.assertEqual(response.status_code, 302)
        evidence = self.order.evidences.get()
        self.assertEqual(evidence.assignment_id, assignment.id)
        self.assertEqual(evidence.created_by_id, self.driver_user.id)

        download_request = RequestFactory().get("/download/", HTTP_HOST="testserver")
        download_request.user = self.driver_user
        download_request.empresa = self.empresa
        download = gruas_views.evidence_download.__wrapped__(download_request, evidence.id)
        self.assertEqual(b"".join(download.streaming_content), png)

        other_driver_user = get_user_model().objects.create_user("driver-other", password="x")
        TowingDriver.objects.create(empresa=self.empresa, user=other_driver_user, nombre="Otro conductor")
        denied_request = RequestFactory().post("/evidencias/", {}, HTTP_HOST="testserver")
        denied_request.user = other_driver_user
        denied_request.empresa = self.empresa
        with self.assertRaises(PermissionDenied):
            gruas_views.driver_evidence_upload.__wrapped__(denied_request, self.order.id)

        foreign = TowingOrder.objects.create(empresa=self.other_empresa, numero="GR-EXT-001", origen="X", destino="Y")
        foreign_request = RequestFactory().post("/evidencias/", {}, HTTP_HOST="testserver")
        foreign_request.user = self.driver_user
        foreign_request.empresa = self.empresa
        with self.assertRaises(Http404):
            gruas_views.driver_evidence_upload.__wrapped__(foreign_request, foreign.id)
        evidence.file.delete(save=False)

    def test_evidence_form_rejects_non_image_and_oversized_uploads(self):
        invalid_type = TowingEvidenceForm(data={"kind": "RETIRO"}, files={"file": SimpleUploadedFile("proof.txt", b"not an image", content_type="text/plain")})
        self.assertFalse(invalid_type.is_valid())
        self.assertIn("file", invalid_type.errors)
        oversized = TowingEvidenceForm(data={"kind": "RETIRO"}, files={"file": SimpleUploadedFile("large.png", b"x" * (TowingEvidenceForm.MAX_SIZE + 1), content_type="image/png")})
        self.assertFalse(oversized.is_valid())
        self.assertIn("file", oversized.errors)
