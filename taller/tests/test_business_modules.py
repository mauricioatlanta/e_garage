from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.utils import timezone

from taller.constants.business_modules import (
    MOD_CLIENTES,
    MOD_CONFIGURACION,
    MOD_DESARME,
    MOD_DOCUMENTOS,
    MOD_FLOTA,
    MOD_INICIO,
    MOD_REPUESTOS,
    MOD_SERVICIOS,
    MOD_VEHICULOS,
)
from taller.context_processors.business_modules import business_modules
from taller.forms.onboarding import OnboardingIdentidadForm
from taller.models.configuracion import ConfiguracionEmpresa
from taller.models.empresa import Empresa
from taller.services.business_module_service import BusinessModuleService


class BusinessModuleServiceTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="business-modules-owner",
            email="modules@example.com",
            password="test-password",
        )
        self.empresa = Empresa.objects.create(
            user=self.user,
            nombre_taller="Empresa Módulos",
            pais="CL",
        )
        self.config, _ = ConfiguracionEmpresa.objects.get_or_create(
            empresa=self.empresa
        )

    def test_workshop_activa_modulos_operativos(self):
        self.config.rubro_principal = "WORKSHOP"
        self.config.usa_vehiculos = True
        self.config.usa_servicios = True

        active = BusinessModuleService.get_active_modules(self.config)

        self.assertTrue(
            {
                MOD_INICIO,
                MOD_CLIENTES,
                MOD_DOCUMENTOS,
                MOD_CONFIGURACION,
                MOD_VEHICULOS,
                MOD_REPUESTOS,
                MOD_SERVICIOS,
            }.issubset(active)
        )
        self.assertNotIn(MOD_DESARME, active)
        self.assertNotIn(MOD_FLOTA, active)

    def test_parts_no_activa_vehiculos_ni_servicios(self):
        self.config.rubro_principal = "PARTS"
        self.config.rubros = []
        self.config.usa_vehiculos = True
        self.config.usa_servicios = True

        active = BusinessModuleService.get_active_modules(self.config)

        self.assertIn(MOD_REPUESTOS, active)
        self.assertNotIn(MOD_VEHICULOS, active)
        self.assertNotIn(MOD_SERVICIOS, active)
        self.assertNotIn(MOD_DESARME, active)
        self.assertNotIn(MOD_FLOTA, active)

    def test_mixed_activa_desarme(self):
        self.config.rubro_principal = "MIXED"
        self.config.usa_vehiculos = True
        self.config.usa_servicios = True

        active = BusinessModuleService.get_active_modules(self.config)

        self.assertIn(MOD_DESARME, active)
        self.assertIn(MOD_VEHICULOS, active)
        self.assertIn(MOD_REPUESTOS, active)
        self.assertIn(MOD_SERVICIOS, active)

    def test_fleet_activa_flota(self):
        self.config.rubro_principal = "FLEET"
        self.config.usa_vehiculos = True
        self.config.usa_servicios = True

        active = BusinessModuleService.get_active_modules(self.config)

        self.assertIn(MOD_FLOTA, active)
        self.assertIn(MOD_VEHICULOS, active)
        self.assertIn(MOD_REPUESTOS, active)
        self.assertIn(MOD_SERVICIOS, active)

    def test_flags_explicitos_descartan_vehiculos_y_servicios(self):
        self.config.rubro_principal = "WORKSHOP"
        self.config.usa_vehiculos = False
        self.config.usa_servicios = False

        active = BusinessModuleService.get_active_modules(self.config)

        self.assertNotIn(MOD_VEHICULOS, active)
        self.assertNotIn(MOD_SERVICIOS, active)
        self.assertIn(MOD_REPUESTOS, active)

    def test_rubros_extra_agregan_modulos(self):
        self.config.rubro_principal = "PARTS"
        self.config.rubros = ["MIXED"]
        self.config.usa_vehiculos = True
        self.config.usa_servicios = True

        active = BusinessModuleService.get_active_modules(self.config)

        self.assertIn(MOD_REPUESTOS, active)
        self.assertIn(MOD_DESARME, active)
        self.assertIn(MOD_VEHICULOS, active)
        self.assertIn(MOD_SERVICIOS, active)

    def test_nav_items_respeta_orden_url_y_ruta_activa(self):
        self.config.rubro_principal = "PARTS"
        self.config.rubros = []

        items = BusinessModuleService.get_nav_items(
            self.config,
            url_prefix="/cl/es",
            current_path="/cl/es/repuestos/",
        )

        keys = [item["key"] for item in items]

        self.assertEqual(
            keys,
            [
                MOD_INICIO,
                MOD_CLIENTES,
                MOD_DOCUMENTOS,
                MOD_REPUESTOS,
                MOD_CONFIGURACION,
            ],
        )

        repuestos = next(item for item in items if item["key"] == MOD_REPUESTOS)
        self.assertEqual(repuestos["url"], "/cl/es/repuestos/")
        self.assertTrue(repuestos["is_active"])

        inicio = next(item for item in items if item["key"] == MOD_INICIO)
        self.assertFalse(inicio["is_active"])


class ModuleConfigurationStateTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="module-state-owner",
            email="state@example.com",
            password="test-password",
        )
        self.empresa = Empresa.objects.create(
            user=self.user,
            nombre_taller="Empresa Estado",
            pais="CL",
        )
        self.config, _ = ConfiguracionEmpresa.objects.get_or_create(
            empresa=self.empresa
        )

    def test_onboarding_incompleto_no_requiere_configuracion(self):
        self.empresa.onboarding_completado = False
        self.empresa.save(update_fields=["onboarding_completado"])
        self.config.modules_configured_at = None
        self.config.save(update_fields=["modules_configured_at"])

        result = BusinessModuleService.needs_module_configuration(self.empresa)

        self.assertFalse(result)

    def test_onboarding_completo_sin_fecha_requiere_configuracion(self):
        self.empresa.onboarding_completado = True
        self.empresa.save(update_fields=["onboarding_completado"])
        self.config.modules_configured_at = None
        self.config.save(update_fields=["modules_configured_at"])

        result = BusinessModuleService.needs_module_configuration(self.empresa)

        self.assertTrue(result)

    def test_onboarding_completo_con_fecha_no_requiere_configuracion(self):
        self.empresa.onboarding_completado = True
        self.empresa.save(update_fields=["onboarding_completado"])
        self.config.modules_configured_at = timezone.now()
        self.config.save(update_fields=["modules_configured_at"])

        result = BusinessModuleService.needs_module_configuration(self.empresa)

        self.assertFalse(result)

    def test_mark_modules_configured_persiste_fecha(self):
        self.config.modules_configured_at = None
        self.config.save(update_fields=["modules_configured_at"])

        BusinessModuleService.mark_modules_configured(self.config)

        self.config.refresh_from_db()
        self.assertIsNotNone(self.config.modules_configured_at)


class OnboardingIdentidadFormTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="onboarding-modules-owner",
            email="onboarding@example.com",
            password="test-password",
        )
        self.empresa = Empresa.objects.create(
            user=self.user,
            nombre_taller="Nombre Anterior",
            pais="CL",
        )
        self.config, _ = ConfiguracionEmpresa.objects.get_or_create(
            empresa=self.empresa
        )
        self.config.modules_configured_at = None
        self.config.save(update_fields=["modules_configured_at"])

    def test_save_guarda_rubro_y_modules_configured_at(self):
        form = OnboardingIdentidadForm(
            data={
                "nombre_taller": "Empresa Actualizada",
                "lema": "Servicio automotriz profesional",
                "rubro_principal": "PARTS",
            },
            instance=self.empresa,
        )

        self.assertTrue(form.is_valid(), form.errors)

        empresa = form.save()
        empresa.refresh_from_db()
        self.config.refresh_from_db()

        self.assertEqual(empresa.nombre_taller, "Empresa Actualizada")
        self.assertEqual(self.config.rubro_principal, "PARTS")
        self.assertEqual(
            self.config.tagline,
            "Servicio automotriz profesional",
        )
        self.assertIsNotNone(self.config.modules_configured_at)


class BusinessModulesContextProcessorTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="context-modules-owner",
            email="context@example.com",
            password="test-password",
        )
        self.empresa = Empresa.objects.create(
            user=self.user,
            nombre_taller="Empresa Contexto",
            pais="CL",
        )
        self.config, _ = ConfiguracionEmpresa.objects.get_or_create(
            empresa=self.empresa
        )
        self.factory = RequestFactory()

    def test_usuario_anonimo_no_recibe_contexto(self):
        request = self.factory.get("/cl/es/dashboard/")

        result = business_modules(request)

        self.assertEqual(result, {})

    def test_usuario_autenticado_recibe_modulos_y_navegacion(self):
        self.empresa.onboarding_completado = True
        self.empresa.save(update_fields=["onboarding_completado"])

        self.config.rubro_principal = "PARTS"
        self.config.rubros = []
        self.config.modules_configured_at = None
        self.config.save(
            update_fields=[
                "rubro_principal",
                "rubros",
                "modules_configured_at",
            ]
        )

        request = self.factory.get("/cl/es/repuestos/")
        request.user = self.user

        result = business_modules(request)

        self.assertIn("business_modules", result)
        self.assertIn("nav_items", result)
        self.assertIn("needs_module_config", result)

        self.assertIn(MOD_REPUESTOS, result["business_modules"])
        self.assertNotIn(MOD_VEHICULOS, result["business_modules"])
        self.assertNotIn(MOD_SERVICIOS, result["business_modules"])
        self.assertTrue(result["needs_module_config"])

        repuestos = next(
            item
            for item in result["nav_items"]
            if item["key"] == MOD_REPUESTOS
        )
        self.assertEqual(repuestos["url"], "/cl/es/repuestos/")
        self.assertTrue(repuestos["is_active"])

    def test_context_processor_detecta_prefijo_usa_ingles(self):
        self.config.rubro_principal = "PARTS"
        self.config.rubros = []
        self.config.save(update_fields=["rubro_principal", "rubros"])

        request = self.factory.get("/us/en/repuestos/")
        request.user = self.user

        result = business_modules(request)

        repuestos = next(
            item
            for item in result["nav_items"]
            if item["key"] == MOD_REPUESTOS
        )
        self.assertEqual(repuestos["url"], "/us/en/repuestos/")
