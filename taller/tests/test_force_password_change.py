from django.contrib import admin
from django.contrib.auth.models import AnonymousUser, User
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase

from taller.auth.password_policy import set_user_must_change_password, user_must_change_password
from taller.admin import AdminClienteCreationForm, UserAdmin
from taller.middleware.force_password_change import ForcePasswordChangeMiddleware
from taller.models.configuracion import ConfiguracionEmpresa
from taller.models.empresa import Empresa
from taller.models.perfil_usuario import PerfilUsuario


class ForcePasswordChangeTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def _request(self, path, user):
        request = self.factory.get(path)
        request.user = user
        SessionMiddleware(lambda req: None).process_request(request)
        request.session.save()
        request._messages = FallbackStorage(request)
        return request

    def test_user_property_reads_profile_flag(self):
        user = User.objects.create_user("cliente", password="Temporal123!")
        PerfilUsuario.objects.update_or_create(
            user=user,
            defaults={"must_change_password": True},
        )

        self.assertTrue(user_must_change_password(user))
        self.assertTrue(user.must_change_password)

        set_user_must_change_password(user, False)

        self.assertFalse(user_must_change_password(user))

    def test_middleware_redirects_forced_user(self):
        user = User.objects.create_user("cliente", password="Temporal123!")
        PerfilUsuario.objects.update_or_create(
            user=user,
            defaults={"must_change_password": True},
        )
        request = self._request("/cl/es/dashboard/", user)
        middleware = ForcePasswordChangeMiddleware(lambda req: None)

        response = middleware(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/cl/es/accounts/password/force/")

    def test_middleware_allows_force_view_logout_static_and_superuser(self):
        user = User.objects.create_user("cliente", password="Temporal123!")
        PerfilUsuario.objects.update_or_create(
            user=user,
            defaults={"must_change_password": True},
        )
        superuser = User.objects.create_superuser("root", "root@example.com", "x")
        middleware = ForcePasswordChangeMiddleware(lambda req: "ok")

        self.assertEqual(middleware(self._request("/cl/es/accounts/password/force/", user)), "ok")
        self.assertEqual(middleware(self._request("/accounts/logout/", user)), "ok")
        self.assertEqual(middleware(self._request("/static/app.css", user)), "ok")
        self.assertEqual(middleware(self._request("/admin/", superuser)), "ok")
        self.assertEqual(middleware(self._request("/admin/", AnonymousUser())), "ok")

    def test_admin_add_form_creates_company_rubro_and_forced_password_flag(self):
        form = AdminClienteCreationForm(
            data={
                "username": "cliente-admin@example.com",
                "password1": "Eg-Temporal99-Aa1!",
                "password2": "Eg-Temporal99-Aa1!",
                "first_name": "Cliente",
                "last_name": "Demo",
                "nombre_taller": "Repuestos Demo",
                "telefono": "+56911112222",
                "pais": "CL",
                "rubro_principal": "WORKSHOP",
                "plan": "trial",
                "dias_prueba": 14,
            }
        )
        self.assertTrue(form.is_valid(), form.errors)

        user = form.save(commit=False)
        request = self.factory.post("/admin/auth/user/add/")
        request.user = User.objects.create_superuser("root_admin", "root@example.com", "x")

        UserAdmin(User, admin.site).save_model(request, user, form, change=False)

        empresa = Empresa.objects.get(user=user)
        config = ConfiguracionEmpresa.objects.get(empresa=empresa)
        perfil = PerfilUsuario.objects.get(user=user)

        self.assertEqual(empresa.nombre_taller, "Repuestos Demo")
        self.assertEqual(empresa.plan, "trial")
        self.assertEqual(empresa.dias_prueba, 14)
        self.assertEqual(user.email, "cliente-admin@example.com")
        self.assertEqual(config.rubro_principal, "WORKSHOP")
        self.assertEqual(config.rubros, ["WORKSHOP"])
        self.assertTrue(perfil.must_change_password)
