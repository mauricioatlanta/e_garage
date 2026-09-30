from django.contrib.auth.models import Group
from django.test import TestCase

from taller.models.documento import Documento
from taller.tests.factories import DocumentoFactory, EmpresaFactory


class DocumentoEstadoOperativoOTTests(TestCase):
    def test_ot_defaults_to_ingresado(self):
        documento = DocumentoFactory(tipo="OT", estado_operativo_ot="")

        documento.refresh_from_db()

        self.assertEqual(documento.estado_operativo_ot, Documento.ESTADO_OT_INGRESADO)

    def test_presupuesto_keeps_operational_state_blank(self):
        documento = DocumentoFactory(tipo="PRES")

        documento.refresh_from_db()

        self.assertEqual(documento.estado_operativo_ot, "")

    def test_update_operational_state_does_not_change_accounting_state(self):
        empresa = EmpresaFactory()
        Group.objects.get_or_create(name="Owner")[0].user_set.add(empresa.user)
        documento = DocumentoFactory(
            empresa=empresa,
            tipo="OT",
            estado="BORRADOR",
            estado_operativo_ot=Documento.ESTADO_OT_INGRESADO,
        )
        self.client.force_login(empresa.user)

        response = self.client.post(
            f"/cl/documentos/ver/{documento.pk}/estado-operativo/",
            {"estado_operativo_ot": Documento.ESTADO_OT_EN_REPARACION},
        )

        self.assertEqual(response.status_code, 302)
        documento.refresh_from_db()
        self.assertEqual(documento.estado, "BORRADOR")
        self.assertEqual(documento.estado_operativo_ot, Documento.ESTADO_OT_EN_REPARACION)
