from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase

from taller.models.clientes import Cliente
from taller.models.empresa import Empresa
from taller.models.extras_vehiculo import (
    CajaVehiculo,
    CajaVehiculoEmpresa,
    MotorVehiculo,
    MotorVehiculoEmpresa,
)
from taller.models.marca import Marca
from taller.models.modelo import Modelo
from taller.vehiculos.forms import VehiculoForm


class VehiculoFormFreeTextTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="vehiculo_free_text_user",
            password="testpass123",
        )
        from taller.tests.factories import EmpresaFactory
        self.empresa = EmpresaFactory(
            user=self.user,
            nombre_taller="Taller Vehiculo Form",
            pais="CL",
            moneda="CLP",
            zona_horaria="America/Santiago",
        )
        self.cliente = Cliente.objects.create(
            empresa=self.empresa,
            nombre="Cliente Vehiculo",
            tax_id="11-1",
        )
        self.marca = Marca.objects.create(nombre="Chevrolet", country="CL")
        self.modelo = Modelo.objects.create(nombre="Camaro", marca=self.marca, country="CL")
        self.factory = RequestFactory()

    def test_form_acepta_motor_y_caja_como_texto_libre(self):
        data = {
            "cliente": str(self.cliente.pk),
            "patente": "TAG123",
            "vin": "VIN-TAG-123",
            "anio": "2024",
            "marca": str(self.marca.pk),
            "modelo": str(self.modelo.pk),
            "motor": "5.7 V8",
            "caja": "Automatica 8AT",
        }
        request = self.factory.post("/cl/es/vehiculos/crear/", data=data)
        request.user = self.user

        form = VehiculoForm(data=data, user=self.user, request=request)

        self.assertTrue(form.is_valid(), form.errors.as_json())

        vehiculo = form.save(commit=False)
        vehiculo.empresa = self.empresa
        vehiculo.save()

        self.assertIsNone(vehiculo.motor)
        self.assertIsNone(vehiculo.caja)
        self.assertEqual(vehiculo.motor_empresa.nombre, "5.7 V8")
        self.assertEqual(vehiculo.caja_empresa.nombre, "Automatica 8AT")
        self.assertFalse(MotorVehiculo.objects.filter(nombre="5.7 V8", country="CL").exists())
        self.assertFalse(
            CajaVehiculo.objects.filter(nombre="Automatica 8AT", country="CL").exists()
        )
        self.assertTrue(
            MotorVehiculoEmpresa.objects.filter(
                empresa=self.empresa,
                modelo=self.modelo,
                nombre="5.7 V8",
                country="CL",
            ).exists()
        )
        self.assertTrue(
            CajaVehiculoEmpresa.objects.filter(
                empresa=self.empresa,
                modelo=self.modelo,
                nombre="Automatica 8AT",
                country="CL",
            ).exists()
        )
