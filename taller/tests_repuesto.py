from django.test import TestCase
from taller.models.repuesto import Repuesto
from taller.models.empresa import Empresa
from taller.forms.repuesto import RepuestoForm

class RepuestoFormTest(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(nombre_taller="Empresa Test", empresa="Empresa Test")
        from taller.models.tienda import Tienda
        self.tienda = Tienda.objects.create(nombre="Tienda Test")

    def test_precio_fields_formatting_and_saving(self):
        data = {
            'tienda': self.tienda.id,
            'nombre_repuesto': 'Filtro de aceite',
            'part_number': 'ABC123',
            'stock': 10,
            'precio_compra': '$12.345',
            'precio_venta': '$15.678',
        }
        form = RepuestoForm(data)
        self.assertTrue(form.is_valid(), form.errors)
        repuesto = form.save(commit=False)
        repuesto.empresa = self.empresa
        repuesto.save()
        self.assertEqual(repuesto.precio_compra, 12345)
        self.assertEqual(repuesto.precio_venta, 15678)
