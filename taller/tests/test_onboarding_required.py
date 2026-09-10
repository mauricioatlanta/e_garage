import importlib

from django.http import HttpResponse
from django.test import Client, RequestFactory, TestCase, override_settings
from django.urls import resolve

from taller.forms.onboarding import OnboardingIdentidadForm
from taller.middleware.onboarding_middleware import OnboardingMiddleware
from taller.models.configuracion import ConfiguracionEmpresa
from taller.models.team_member import TeamMember
from taller.models.tecnico import Tecnico
from taller.services.onboarding_service import OnboardingService, language_code_for_request
from taller.services.registration_service import RegistrationService
from taller.tests.factories import EmpresaFactory, UserFactory


def _response(_request):
    return HttpResponse("ok")


class OnboardingRequiredMiddlewareTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = OnboardingMiddleware(_response)

    def _request(self, path, empresa=None, user=None):
        request = self.factory.get(path)
        request.user = user or empresa.user
        request.empresa = empresa
        return request

    def test_legacy_grandfathered_company_is_not_blocked(self):
        empresa = EmpresaFactory(onboarding_completado=True)

        response = self.middleware(self._request("/cl/es/clientes/", empresa))

        self.assertEqual(response.status_code, 200)

    def test_new_owner_incomplete_is_redirected_from_workspace_and_dashboard(self):
        empresa = EmpresaFactory(onboarding_completado=False, onboarding_step=1)

        for path in ("/cl/es/workspace/", "/cl/es/dashboard/"):
            response = self.middleware(self._request(path, empresa))
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response["Location"], "/cl/es/onboarding/identidad/")

    def test_direct_operational_urls_are_blocked_by_allowlist_policy(self):
        empresa = EmpresaFactory(onboarding_completado=False, onboarding_step=1)

        for path in (
            "/cl/es/clientes/",
            "/cl/es/vehiculos/",
            "/cl/es/documentos/",
            "/cl/es/repuestos/",
            "/cl/es/reportes/",
        ):
            response = self.middleware(self._request(path, empresa))
            self.assertEqual(response.status_code, 302, path)
            self.assertEqual(response["Location"], "/cl/es/onboarding/identidad/")

    def test_allowed_routes_do_not_redirect_during_onboarding(self):
        empresa = EmpresaFactory(onboarding_completado=False)

        for path in (
            "/cl/es/onboarding/identidad/",
            "/accounts/logout/",
            "/cl/es/accounts/password/reset/",
            "/static/app.css",
            "/media/logo.png",
            "/cl/es/help/",
        ):
            response = self.middleware(self._request(path, empresa))
            self.assertEqual(response.status_code, 200, path)

    def test_staff_superuser_and_unrelated_user_are_not_trapped(self):
        empresa = EmpresaFactory(onboarding_completado=False)
        staff = UserFactory(is_staff=True)
        superuser = UserFactory(is_superuser=True, is_staff=True)
        other_user = UserFactory()

        for user in (staff, superuser):
            response = self.middleware(self._request("/cl/es/clientes/", empresa, user=user))
            self.assertEqual(response.status_code, 200)

        request = self.factory.get("/cl/es/clientes/")
        request.user = other_user
        request.empresa = None
        response = self.middleware(request)
        self.assertEqual(response.status_code, 200)

    def test_active_team_member_cannot_bypass_incomplete_company_onboarding(self):
        empresa = EmpresaFactory(onboarding_completado=False, onboarding_step=1)
        member = UserFactory()
        TeamMember.objects.create(user=member, empresa=empresa, rol="Vendedor", is_active=True)

        response = self.middleware(self._request("/cl/es/clientes/", empresa, user=member))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/cl/es/onboarding/identidad/")

    def test_country_aware_onboarding_redirects(self):
        cl = EmpresaFactory(pais="CL", onboarding_completado=False)
        us = EmpresaFactory(pais="US", onboarding_completado=False)

        cl_response = self.middleware(self._request("/cl/es/workspace/", cl))
        us_response = self.middleware(self._request("/us/en/workspace/", us))
        us_short_response = self.middleware(self._request("/us/workspace/", us))

        self.assertEqual(cl_response["Location"], "/cl/es/onboarding/identidad/")
        self.assertEqual(us_response["Location"], "/us/en/onboarding/identidad/")
        self.assertEqual(us_short_response["Location"], "/us/en/onboarding/identidad/")

    def test_agregar_tecnico_route_is_not_shadowed_by_step_route(self):
        expected = {
            "/cl/es/onboarding/agregar-tecnico/": "onboarding_agregar_tecnico",
            "/cl/es/onboarding/preview-documento/": "onboarding_preview_documento",
            "/us/en/onboarding/agregar-tecnico/": "onboarding_agregar_tecnico",
            "/us/en/onboarding/preview-documento/": "onboarding_preview_documento",
            "/us/es/onboarding/agregar-tecnico/": "onboarding_agregar_tecnico",
            "/us/es/onboarding/preview-documento/": "onboarding_preview_documento",
        }
        for path, view_name in expected.items():
            match = resolve(path)
            self.assertEqual(match.func.__name__, view_name)


class OnboardingRequiredStateTests(TestCase):
    def test_registration_service_creates_new_company_pending_onboarding(self):
        user = UserFactory(email="new-owner@example.com")
        result = RegistrationService.create_company_for_user(
            user=user,
            company_data={
                "nombre_taller": "",
                "pais": "CL",
                "telefono": "+56912345678",
            },
            rubros_list=["WORKSHOP"],
        )

        empresa = result["empresa"]
        self.assertFalse(empresa.onboarding_completado)
        self.assertEqual(empresa.onboarding_step, 1)

    def test_grandfather_migration_marks_existing_empresas_complete(self):
        empresa = EmpresaFactory(onboarding_completado=False, onboarding_completed_at=None)
        migration = importlib.import_module(
            "taller.migrations.0179_grandfather_existing_empresas_onboarding"
        )

        migration.grandfather_existing_empresas(importlib.import_module("django.apps").apps, None)

        empresa.refresh_from_db()
        self.assertTrue(empresa.onboarding_completado)
        self.assertIsNotNone(empresa.onboarding_completed_at)

    def test_identity_requires_real_name_phone_rubro_and_contact_data(self):
        user = UserFactory(first_name="Usuario", username="usuario")
        empresa = EmpresaFactory(
            user=user,
            nombre_taller="Taller de Usuario",
            telefono="",
            email="owner@example.com",
            direccion="",
            onboarding_completado=False,
        )
        ConfiguracionEmpresa.objects.create(empresa=empresa)

        form = OnboardingIdentidadForm(
            data={
                "nombre_taller": "Taller de Usuario",
                "telefono": "",
                "email": "owner@example.com",
                "direccion": "",
                "rubro_principal": "",
            },
            instance=empresa,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("nombre_taller", form.errors)
        self.assertIn("telefono", form.errors)
        self.assertIn("direccion", form.errors)
        self.assertIn("rubro_principal", form.errors)

    def test_identity_rejects_only_exact_generated_placeholder_name(self):
        user = UserFactory(first_name="Jorge", username="jorge")
        empresa = EmpresaFactory(
            user=user,
            nombre_taller="Taller de Jorge",
            onboarding_completado=False,
            with_config=True,
        )

        placeholder_form = OnboardingIdentidadForm(
            data={
                "nombre_taller": "Taller de Jorge",
                "telefono": "+56912345678",
                "email": "jorge@example.test",
                "direccion": "Alameda 123",
                "rubro_principal": "WORKSHOP",
            },
            instance=empresa,
        )
        self.assertFalse(placeholder_form.is_valid())
        self.assertIn("nombre_taller", placeholder_form.errors)

        real_business_form = OnboardingIdentidadForm(
            data={
                "nombre_taller": "Taller de Frenos San Martín",
                "telefono": "+56912345678",
                "email": "frenos@example.test",
                "direccion": "Alameda 123",
                "rubro_principal": "WORKSHOP",
            },
            instance=empresa,
        )
        self.assertTrue(real_business_form.is_valid(), real_business_form.errors)

        other_user = UserFactory(first_name="Maria", username="maria")
        other_empresa = EmpresaFactory(
            user=other_user,
            nombre_taller="Taller de Jorge",
            onboarding_completado=False,
            with_config=True,
        )
        same_name_different_user_form = OnboardingIdentidadForm(
            data={
                "nombre_taller": "Taller de Jorge",
                "telefono": "+56912345678",
                "email": "jorge-real@example.test",
                "direccion": "Alameda 123",
                "rubro_principal": "WORKSHOP",
            },
            instance=other_empresa,
        )
        self.assertTrue(
            same_name_different_user_form.is_valid(),
            same_name_different_user_form.errors,
        )

    def test_identity_persists_empresa_and_configuracion_contact_fields(self):
        empresa = EmpresaFactory(onboarding_completado=False, with_config=True)

        form = OnboardingIdentidadForm(
            data={
                "nombre_taller": "Servicio Automotriz Alameda",
                "telefono": "+56912345678",
                "email": "contacto@alameda.test",
                "direccion": "Alameda 123, Santiago",
                "lema": "Diagnóstico y reparación",
                "rubro_principal": "WORKSHOP",
            },
            instance=empresa,
        )

        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        empresa.refresh_from_db()
        empresa.config.refresh_from_db()

        self.assertEqual(empresa.nombre_taller, "Servicio Automotriz Alameda")
        self.assertEqual(empresa.telefono, "+56912345678")
        self.assertEqual(empresa.email, "contacto@alameda.test")
        self.assertEqual(empresa.direccion, "Alameda 123, Santiago")
        self.assertEqual(empresa.config.rubro_principal, "WORKSHOP")
        self.assertEqual(empresa.config.telefono, "+56912345678")
        self.assertEqual(empresa.config.email_contacto, "contacto@alameda.test")
        self.assertEqual(empresa.config.direccion, "Alameda 123, Santiago")

    def test_identity_accepts_and_persists_signup_supported_rubros(self):
        for idx, rubro in enumerate(("RECYCLING", "TIRE", "DESARMADURIA", "ELECTRIC", "MIXED")):
            empresa = EmpresaFactory(onboarding_completado=False, with_config=True)
            form = OnboardingIdentidadForm(
                data={
                    "nombre_taller": f"Negocio {rubro}",
                    "telefono": f"+56912345{idx:03d}",
                    "email": f"{rubro.lower()}@example.test",
                    "direccion": "Alameda 123, Santiago",
                    "rubro_principal": rubro,
                },
                instance=empresa,
            )

            self.assertTrue(form.is_valid(), form.errors)
            form.save()
            empresa.config.refresh_from_db()
            self.assertEqual(empresa.config.rubro_principal, rubro)
            self.assertIn(rubro, empresa.config.rubros)

    def test_language_code_respects_country_language_prefix(self):
        factory = RequestFactory()

        self.assertEqual(language_code_for_request(factory.get("/cl/es/onboarding/")), "es")
        self.assertEqual(language_code_for_request(factory.get("/us/en/onboarding/")), "en")
        self.assertEqual(language_code_for_request(factory.get("/us/es/onboarding/")), "es")
        self.assertEqual(
            language_code_for_request(factory.get("/workspace/"), EmpresaFactory(pais="BR")),
            "pt",
        )


class OnboardingRequiredWizardTests(TestCase):
    def setUp(self):
        self.client = Client()

    def _incomplete_empresa(self, *, pais="CL"):
        empresa = EmpresaFactory(
            pais=pais,
            nombre_taller="Taller de user",
            telefono="+56912345678" if pais == "CL" else "+13055551234",
            email="owner@example.com",
            direccion="Av Siempre Viva 123",
            onboarding_completado=False,
            onboarding_step=1,
            with_config=True,
        )
        self.client.force_login(empresa.user)
        return empresa

    @override_settings(ALLOWED_HOSTS=["testserver"])
    def test_onboarding_accessible_and_finalization_requires_all_requirements(self):
        empresa = self._incomplete_empresa()

        response = self.client.get("/cl/es/onboarding/identidad/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="RECYCLING"')
        self.assertContains(response, 'value="TIRE"')

        response = self.client.post("/cl/es/onboarding/guardar/3/")
        self.assertEqual(response.status_code, 400)
        empresa.refresh_from_db()
        self.assertFalse(empresa.onboarding_completado)

    @override_settings(ALLOWED_HOSTS=["testserver"])
    def test_full_cl_flow_completes_and_redirects_to_cl_workspace(self):
        empresa = self._incomplete_empresa(pais="CL")

        response = self.client.post(
            "/cl/es/onboarding/guardar/1/",
            {
                "nombre_taller": "Taller Alameda",
                "telefono": "+56912345678",
                "email": "contacto@alameda.test",
                "direccion": "Alameda 123",
                "rubro_principal": "WORKSHOP",
            },
        )
        self.assertEqual(response.json()["next_step_url"], "/cl/es/onboarding/equipo/")

        response = self.client.post(
            "/cl/es/onboarding/guardar/2/",
            {
                "nombre": "Ana Torres",
                "telefono": "+56987654321",
                "direccion": "Alameda 123",
                "rol": "Técnico",
            },
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertTrue(response.json().get("success"), response.content)
        self.assertEqual(response.json()["next_step_url"], "/cl/es/onboarding/finalizar/")

        response = self.client.post("/cl/es/onboarding/guardar/3/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["redirect_url"], "/cl/es/workspace/")
        empresa.refresh_from_db()
        self.assertTrue(empresa.onboarding_completado)
        self.assertIsNotNone(empresa.onboarding_completed_at)

    @override_settings(ALLOWED_HOSTS=["testserver"])
    def test_full_us_flow_does_not_redirect_to_chile(self):
        empresa = self._incomplete_empresa(pais="US")

        self.client.post(
            "/us/en/onboarding/guardar/1/",
            {
                "nombre_taller": "Main Street Auto",
                "telefono": "+13055551234",
                "email": "contact@mainstreet.test",
                "direccion": "100 Main St, Miami",
                "rubro_principal": "WORKSHOP",
            },
        )
        response = self.client.post(
            "/us/en/onboarding/guardar/2/",
            {
                "nombre": "John Miller",
                "telefono": "+13055559876",
                "direccion": "100 Main St",
                "rol": "Technician",
            },
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertTrue(response.json().get("success"), response.content)

        response = self.client.post("/us/en/onboarding/guardar/3/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["redirect_url"], "/us/en/workspace/")
        empresa.refresh_from_db()
        self.assertTrue(empresa.onboarding_completado)

    @override_settings(ALLOWED_HOSTS=["testserver"])
    def test_team_requirement_uses_tecnico_with_tenant_isolation(self):
        empresa = self._incomplete_empresa()
        other_empresa = EmpresaFactory(onboarding_completado=False)
        Tecnico.objects.create(
            empresa=other_empresa,
            nombre="Otro Técnico",
            telefono="+56911111111",
            rol="Técnico",
            activo=True,
        )

        self.client.post(
            "/cl/es/onboarding/guardar/1/",
            {
                "nombre_taller": "Taller Alameda",
                "telefono": "+56912345678",
                "email": "contacto@alameda.test",
                "direccion": "Alameda 123",
                "rubro_principal": "WORKSHOP",
            },
        )

        response = self.client.post("/cl/es/onboarding/guardar/3/")
        self.assertEqual(response.status_code, 400)

        response = self.client.post(
            "/cl/es/onboarding/guardar/2/",
            {
                "nombre": "Ana Torres",
                "telefono": "+56987654321",
                "rol": "Técnico",
            },
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertTrue(response.json().get("success"), response.content)
        self.assertTrue(OnboardingService.has_operational_team(empresa))
        self.assertEqual(Tecnico.objects.filter(empresa=empresa).count(), 1)

    @override_settings(ALLOWED_HOSTS=["testserver"])
    def test_auxiliary_add_tecnico_endpoint_uses_team_validation_and_does_not_skip_steps(self):
        empresa = self._incomplete_empresa()

        self.client.post(
            "/cl/es/onboarding/guardar/1/",
            {
                "nombre_taller": "Taller Alameda",
                "telefono": "+56912345678",
                "email": "contacto@alameda.test",
                "direccion": "Alameda 123",
                "rubro_principal": "WORKSHOP",
            },
        )
        empresa.refresh_from_db()
        self.assertEqual(empresa.onboarding_step, 2)

        response = self.client.post(
            "/cl/es/onboarding/agregar-tecnico/",
            {"nombre": "Ana Torres", "rol": ""},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json().get("success"))
        self.assertIn("telefono", response.json()["errors"])
        self.assertEqual(Tecnico.objects.filter(empresa=empresa).count(), 0)

        response = self.client.post(
            "/cl/es/onboarding/agregar-tecnico/",
            {
                "nombre": "Ana Torres",
                "telefono": "+56987654321",
                "direccion": "Alameda 123",
                "rol": "Técnico",
            },
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertTrue(response.json().get("success"), response.content)
        self.assertTrue(OnboardingService.has_operational_team(empresa))

        empresa.refresh_from_db()
        self.assertEqual(empresa.onboarding_step, 2)
        response = self.client.post("/cl/es/onboarding/guardar/3/")
        self.assertEqual(response.status_code, 400)
        empresa.refresh_from_db()
        self.assertFalse(empresa.onboarding_completado)
