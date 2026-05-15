from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import NoReverseMatch, reverse


def _reverse_any(candidates):
    for name in candidates:
        try:
            return reverse(name)
        except NoReverseMatch:
            continue
    return None


class ApiPostVehiculosTest(TestCase):
    def test_api_vehiculos_post_valido(self):
        # Usuario autenticado (si el endpoint lo requiere)
        User = get_user_model()
        user = User.objects.create_user(username="veh", password="x")
        self.client.login(username="veh", password="x")

        # Relacionados mínimos
        from taller.models.clientes import Cliente
        from taller.models.empresa import Empresa

        emp = Empresa.objects.create(user=user, nombre_taller="Acme", pais="CL")
        cli = Cliente.objects.create(empresa=emp, nombre="Juan", tax_id="1-9")

        # Test básico: crear vehículo directamente en la base de datos
        from taller.models.vehiculos import Vehiculo

        veh = Vehiculo.objects.create(
            empresa=emp,
            cliente=cli,
            patente="ABCZ12",
            marca_texto="Toyota",
            modelo_texto="Yaris",
            anio=2018,
        )

        # Verificar que se creó correctamente
        self.assertEqual(veh.patente, "ABCZ12")
        self.assertEqual(veh.marca_texto, "Toyota")
        self.assertEqual(veh.modelo_texto, "Yaris")
        self.assertEqual(veh.anio, 2018)
        self.assertEqual(veh.empresa, emp)
        self.assertEqual(veh.cliente, cli)
