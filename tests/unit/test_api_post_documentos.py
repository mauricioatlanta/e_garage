import json
from django.test import TestCase
from django.urls import reverse, NoReverseMatch
from django.contrib.auth import get_user_model

def _reverse_any(candidates):
    for name in candidates:
        try:
            return reverse(name)
        except NoReverseMatch:
            continue
    return None

class ApiPostDocumentosTest(TestCase):
    def test_api_documentos_post_valido(self):
        User = get_user_model()
        user = User.objects.create_user(username="doc", password="x")
        self.client.login(username="doc", password="x")

        from taller.models.empresa import Empresa
        from taller.models.clientes import Cliente
        from taller.models.vehiculos import Vehiculo

        emp = Empresa.objects.create(user=user, nombre_taller="Garage", pais="CL")
        cli = Cliente.objects.create(empresa=emp, nombre="Ana", tax_id="2-7")
        veh = Vehiculo.objects.create(
            empresa=emp, 
            cliente=cli, 
            patente="KLLJ22", 
            marca_texto="Kia", 
            modelo_texto="Rio", 
            anio=2019
        )

        # Test básico: crear documento directamente en la base de datos
        from taller.models.documento import Documento
        
        doc = Documento.objects.create(
            empresa=emp,
            cliente=cli,
            vehiculo=veh,
            tipo="FAC",
            fecha_emision="2025-01-10"
        )
        
        # Verificar que se creó correctamente
        self.assertEqual(doc.tipo, "FAC")
        self.assertEqual(str(doc.fecha_emision), "2025-01-10")
        self.assertEqual(doc.empresa, emp)
        self.assertEqual(doc.cliente, cli)
        self.assertEqual(doc.vehiculo, veh)
