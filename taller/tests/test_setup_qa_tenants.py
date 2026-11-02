from io import StringIO
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management import CommandError, call_command
from django.test import TestCase

from taller.models.configuracion import ConfiguracionEmpresa
from taller.models.empresa import Empresa
from taller.models.suscripcion import Suscripcion


class SetupQATenantsCommandTests(TestCase):
    expected = {
        "vc_us_workshop": ("Validation Workshop USA", "WORKSHOP"),
        "vc_us_salvage": ("Validation Salvage Yard USA", "DESARMADURIA"),
        "vc_us_parts": ("Validation Auto Parts USA", "PARTS"),
        "vc_us_tire": ("Validation Tire Shop USA", "TIRE"),
    }

    def run_command(self, *args):
        output = StringIO()
        call_command("setup_qa_tenants", *args, stdout=output)
        return output.getvalue()

    def test_dry_run_does_not_write(self):
        output = self.run_command("--country", "US", "--dry-run")

        self.assertIn("Dry-run: no se escribieron datos.", output)
        self.assertEqual(get_user_model().objects.count(), 0)
        self.assertEqual(Empresa.objects.count(), 0)
        self.assertEqual(ConfiguracionEmpresa.objects.count(), 0)

    def test_creates_exactly_four_minimal_usa_tenants(self):
        self.run_command("--country", "US")

        User = get_user_model()
        self.assertEqual(User.objects.count(), 4)
        self.assertEqual(Empresa.objects.count(), 4)
        self.assertEqual(ConfiguracionEmpresa.objects.count(), 4)
        self.assertEqual(Suscripcion.objects.count(), 0)

        for username, (name, rubro) in self.expected.items():
            user = User.objects.get(username=username)
            empresa = user.empresa
            config = empresa.config
            self.assertEqual(empresa.nombre_taller, name)
            self.assertEqual(empresa.pais, "US")
            self.assertEqual(empresa.moneda, "USD")
            self.assertTrue(empresa.suscripcion_activa)
            self.assertFalse(user.is_staff)
            self.assertFalse(user.is_superuser)
            self.assertFalse(user.has_usable_password())
            self.assertEqual(config.rubro_principal, rubro)
            self.assertEqual(config.rubros, [rubro])
            self.assertEqual(config.moneda, "USD")
            self.assertEqual(config.sales_tax_rate, Decimal("0.00"))
            self.assertEqual(config.tasa_impuesto, Decimal("0.00"))
            self.assertFalse(config.aplicar_impuesto_por_defecto)

    def test_second_run_is_idempotent_and_preserves_ids(self):
        self.run_command("--country", "US")
        ids = {
            username: get_user_model().objects.get(username=username).empresa.pk
            for username in self.expected
        }

        self.run_command("--country", "US")

        self.assertEqual(get_user_model().objects.count(), 4)
        self.assertEqual(Empresa.objects.count(), 4)
        self.assertEqual(
            {
                username: get_user_model().objects.get(username=username).empresa.pk
                for username in self.expected
            },
            ids,
        )

    def test_incompatible_username_aborts_before_writing_any_tenant(self):
        User = get_user_model()
        User.objects.create_user(
            username="vc_us_parts",
            email="someone@example.com",
            password="temporary",
        )

        with self.assertRaises(CommandError):
            self.run_command("--country", "US")

        self.assertEqual(Empresa.objects.count(), 0)
        self.assertEqual(User.objects.count(), 1)

    def test_incompatible_existing_company_aborts(self):
        User = get_user_model()
        user = User.objects.create_user(
            username="vc_us_tire",
            email="vc_us_tire@demo.egarage.com",
            password="temporary",
        )
        Empresa.objects.create(
            user=user,
            nombre_taller="Wrong Tenant",
            pais="CL",
            moneda="CLP",
            suscripcion_activa=True,
        )

        with self.assertRaises(CommandError):
            self.run_command("--country", "US")

        self.assertEqual(Empresa.objects.count(), 1)
        self.assertEqual(Empresa.objects.get(user=user).pais, "CL")

    def test_existing_chile_tenant_is_untouched(self):
        User = get_user_model()
        chile_user = User.objects.create_user(username="vc_taller", email="vc_taller@demo.egarage.cl")
        chile = Empresa.objects.create(
            user=chile_user,
            nombre_taller="Demo Taller AutoShop",
            pais="CL",
            moneda="CLP",
            suscripcion_activa=True,
        )

        self.run_command("--country", "US")

        chile.refresh_from_db()
        self.assertEqual(chile.pais, "CL")
        self.assertEqual(chile.moneda, "CLP")
        self.assertEqual(Empresa.objects.filter(pais="CL").count(), 1)
