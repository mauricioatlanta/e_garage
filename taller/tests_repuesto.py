from django.contrib.auth.models import User
from django.test import TestCase

from taller.forms.repuesto import RepuestoForm
from taller.models.empresa import Empresa
from taller.models.repuesto import CategoriaRepuesto


class RepuestoFormTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="repuesto_test", password="testpass123")
        self.empresa = Empresa.objects.create(
            user=self.user,
            nombre_taller="Empresa Test",
            empresa="Empresa Test",
        )
        self.user.empresa = self.empresa
        from taller.models.tienda import Tienda

        self.tienda = Tienda.objects.create(empresa=self.empresa, nombre="Tienda Test")
        self.categoria = CategoriaRepuesto.objects.create(empresa=self.empresa, nombre="Filtros")

    def test_precio_fields_formatting_and_saving(self):
        data = {
            "nombre": "Filtro de aceite",
            "part_number": "ABC123",
            "categoria": self.categoria.id,
            "cantidad_stock": 10,
            "precio_compra": "12345.00",
            "precio_venta": "15678.00",
            "proveedor": "Tienda Test",
        }
        form = RepuestoForm(data, user=self.user)
        self.assertTrue(form.is_valid(), form.errors)
        repuesto = form.save(commit=False)
        repuesto.empresa = self.empresa
        repuesto.save()
        self.assertEqual(float(repuesto.precio_compra), 12345.0)
        self.assertEqual(float(repuesto.precio_venta), 15678.0)
