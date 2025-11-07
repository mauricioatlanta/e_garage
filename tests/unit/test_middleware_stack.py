from django.test import TestCase, override_settings, Client


class MiddlewareStackTest(TestCase):
    """Tests para middleware en stack"""

    @override_settings(MIDDLEWARE=[
        "django.middleware.common.CommonMiddleware",
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "taller.middleware.company_country.CompanyCountryMiddleware",
    ])
    def test_middleware_in_stack_smoke(self):
        """Test middleware en stack básico"""
        c = Client()
        resp = c.get("/")
        assert resp.status_code in (200, 302)

    @override_settings(MIDDLEWARE=[
        "django.middleware.common.CommonMiddleware",
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "taller.middleware.country_context.CountryContextMiddleware",
    ])
    def test_country_context_middleware_in_stack(self):
        """Test CountryContextMiddleware en stack"""
        c = Client()
        resp = c.get("/")
        assert resp.status_code in (200, 302)

    @override_settings(MIDDLEWARE=[
        "django.middleware.common.CommonMiddleware",
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "taller.middleware.empresa_middleware.EmpresaMiddleware",
    ])
    def test_empresa_middleware_in_stack(self):
        """Test EmpresaMiddleware en stack"""
        c = Client()
        resp = c.get("/")
        assert resp.status_code in (200, 302)

    @override_settings(MIDDLEWARE=[
        "django.middleware.common.CommonMiddleware",
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "taller.middleware.fix_language_middleware.FixLanguageMiddleware",
    ])
    def test_fix_language_middleware_in_stack(self):
        """Test FixLanguageMiddleware en stack"""
        c = Client()
        resp = c.get("/")
        assert resp.status_code in (200, 302)

    @override_settings(MIDDLEWARE=[
        "django.middleware.common.CommonMiddleware",
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "taller.middleware.verificar_suscripcion.VerificarSuscripcionMiddleware",
    ])
    def test_verificar_suscripcion_middleware_in_stack(self):
        """Test VerificarSuscripcionMiddleware en stack"""
        c = Client()
        resp = c.get("/")
        assert resp.status_code in (200, 302)

    @override_settings(MIDDLEWARE=[
        "django.middleware.common.CommonMiddleware",
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "taller.middleware.country_url_migration.CountryURLRedirectMiddleware",
    ])
    def test_country_url_migration_middleware_in_stack(self):
        """Test CountryURLRedirectMiddleware en stack"""
        c = Client()
        resp = c.get("/")
        assert resp.status_code in (200, 302)

    def test_multiple_middleware_in_stack(self):
        """Test múltiples middleware en stack"""
        with override_settings(MIDDLEWARE=[
            "django.middleware.common.CommonMiddleware",
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.contrib.auth.middleware.AuthenticationMiddleware",
            "taller.middleware.company_country.CompanyCountryMiddleware",
            "taller.middleware.country_context.CountryContextMiddleware",
            "taller.middleware.empresa_middleware.EmpresaMiddleware",
        ]):
            c = Client()
            resp = c.get("/")
            assert resp.status_code in (200, 302)

    def test_middleware_with_authenticated_user(self):
        """Test middleware con usuario autenticado"""
        from django.contrib.auth.models import User
        from taller.models.empresa import Empresa

        # Crear usuario y empresa
        user = User.objects.create_user(
            username='testuser_middleware',
            password='testpass'
        )
        emp = Empresa.objects.create(
            nombre_taller="Test Garage",
            pais="CL",
            user=user
        )

        with override_settings(MIDDLEWARE=[
            "django.middleware.common.CommonMiddleware",
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.contrib.auth.middleware.AuthenticationMiddleware",
            "taller.middleware.company_country.CompanyCountryMiddleware",
        ]):
            c = Client()
            c.force_login(user)
            resp = c.get("/")
            assert resp.status_code in (200, 302)

    def test_middleware_with_session(self):
        """Test middleware con sesión"""
        from django.contrib.auth.models import User
        from taller.models.empresa import Empresa

        # Crear usuario y empresa
        user = User.objects.create_user(
            username='testuser_session',
            password='testpass'
        )
        emp = Empresa.objects.create(
            nombre_taller="Test Garage",
            pais="CL",
            user=user
        )

        with override_settings(MIDDLEWARE=[
            "django.middleware.common.CommonMiddleware",
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.contrib.auth.middleware.AuthenticationMiddleware",
            "taller.middleware.company_country.CompanyCountryMiddleware",
        ]):
            c = Client()
            c.force_login(user)
            # Establecer empresa en sesión
            session = c.session
            session['empresa_id'] = emp.id
            session.save()
            resp = c.get("/")
            assert resp.status_code in (200, 302)
