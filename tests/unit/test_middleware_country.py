"""
Tests para middleware de país y empresa - cobertura rápida de middlewares
"""

from django.contrib.auth.models import User
from django.http import HttpResponse
from django.test import RequestFactory, TestCase

from taller.middleware.company_country import CompanyCountryMiddleware
from taller.models.empresa import Empresa


class CompanyCountryMiddlewareTest(TestCase):
    """Tests para CompanyCountryMiddleware"""

    def setUp(self):
        """Setup básico para tests"""
        self.factory = RequestFactory()

        # Crear un get_response dummy para el middleware
        def dummy_get_response(request):
            return HttpResponse("OK")

        self.middleware = CompanyCountryMiddleware(dummy_get_response)

        # Crear empresa
        self.user = User.objects.create_user(username="testuser3", password="testpass")
        self.empresa = Empresa.objects.create(
            nombre_taller="Test Garage", pais="CL", user=self.user
        )

        # Crear usuario
        self.user = User.objects.create_user(username="testuser", password="testpass")

        # Asociar usuario con empresa
        self.empresa.user = self.user
        self.empresa.save()

    def test_middleware_with_empresa_in_session(self):
        """Test middleware con empresa en sesión"""
        request = self.factory.get("/")
        request.session = {"empresa_id": self.empresa.id}
        request.user = self.user

        # Procesar request
        response = self.middleware.process_request(request)

        # Verificar que se estableció la empresa
        self.assertEqual(request.company, self.empresa)
        self.assertEqual(request.country, "CL")
        self.assertIsNone(response)  # Middleware no debería retornar respuesta

    def test_middleware_with_user_empresa(self):
        """Test middleware con empresa del usuario"""
        request = self.factory.get("/")
        request.session = {}  # Sin empresa en sesión
        request.user = self.user

        # Procesar request
        response = self.middleware.process_request(request)

        # Verificar que se estableció la empresa del usuario
        self.assertEqual(request.company, self.empresa)
        self.assertEqual(request.country, "CL")
        self.assertIsNone(response)

    def test_middleware_without_empresa(self):
        """Test middleware sin empresa"""
        # Crear un usuario sin empresa asociada
        user_sin_empresa = User.objects.create_user(
            username="testuser_sin_empresa2", password="testpass"
        )

        request = self.factory.get("/")
        request.session = {}
        request.user = user_sin_empresa

        # Procesar request
        response = self.middleware.process_request(request)

        # Verificar que no se estableció empresa
        self.assertIsNone(request.company)
        self.assertEqual(request.country, "CL")  # Default
        self.assertIsNone(response)

    def test_middleware_with_invalid_empresa_id(self):
        """Test middleware con ID de empresa inválido en sesión"""
        # Crear un usuario sin empresa asociada
        user_sin_empresa = User.objects.create_user(
            username="testuser_sin_empresa", password="testpass"
        )

        request = self.factory.get("/")
        request.session = {"empresa_id": 99999}  # ID inexistente
        request.user = user_sin_empresa

        # Procesar request
        response = self.middleware.process_request(request)

        # Verificar que no se estableció empresa
        self.assertIsNone(request.company)
        self.assertEqual(request.country, "CL")  # Default
        self.assertIsNone(response)

    def test_middleware_with_usa_path(self):
        """Test middleware con ruta USA"""
        request = self.factory.get("/us/dashboard/")
        request.session = {}
        request.user = self.user

        # Procesar request
        response = self.middleware.process_request(request)

        # Verificar que se estableció país USA
        self.assertEqual(request.country, "US")
        self.assertIsNone(response)

    def test_middleware_with_chile_path(self):
        """Test middleware con ruta Chile"""
        request = self.factory.get("/cl/dashboard/")
        request.session = {}
        request.user = self.user

        # Procesar request
        response = self.middleware.process_request(request)

        # Verificar que se estableció país Chile
        self.assertEqual(request.country, "CL")
        self.assertIsNone(response)

    def test_middleware_with_usa_empresa(self):
        """Test middleware con empresa USA"""
        # Crear empresa USA
        user_usa = User.objects.create_user(username="testuser5", password="testpass")
        empresa_usa = Empresa.objects.create(nombre_taller="USA Garage", pais="US", user=user_usa)

        request = self.factory.get("/")
        request.session = {"empresa_id": empresa_usa.id}
        request.user = self.user

        # Procesar request
        response = self.middleware.process_request(request)

        # Verificar que se estableció país USA desde empresa
        self.assertEqual(request.company, empresa_usa)
        self.assertEqual(request.country, "US")
        self.assertIsNone(response)

    def test_middleware_preserves_existing_country(self):
        """Test que middleware preserva país existente"""
        request = self.factory.get("/")
        request.session = {}
        request.user = self.user
        request.country = "US"  # Establecer país previamente

        # Procesar request
        response = self.middleware.process_request(request)

        # Verificar que se preservó el país existente
        self.assertEqual(request.country, "US")
        self.assertIsNone(response)

    def test_middleware_with_anonymous_user(self):
        """Test middleware con usuario anónimo"""
        from django.contrib.auth.models import AnonymousUser

        request = self.factory.get("/")
        request.session = {}
        request.user = AnonymousUser()

        # Procesar request
        response = self.middleware.process_request(request)

        # Verificar que funciona con usuario anónimo
        self.assertIsNone(request.company)
        self.assertEqual(request.country, "CL")  # Default
        self.assertIsNone(response)

    def test_middleware_with_empresa_usa_path_priority(self):
        """Test que ruta USA tiene prioridad sobre empresa"""
        # Crear empresa Chile
        user_chile = User.objects.create_user(username="testuser4", password="testpass")
        empresa_chile = Empresa.objects.create(
            nombre_taller="Chile Garage", pais="CL", user=user_chile
        )

        request = self.factory.get("/us/dashboard/")
        request.session = {"empresa_id": empresa_chile.id}
        request.user = self.user

        # Procesar request
        response = self.middleware.process_request(request)

        # Verificar que ruta USA tiene prioridad
        self.assertEqual(request.company, empresa_chile)
        self.assertEqual(request.country, "US")  # Ruta tiene prioridad
        self.assertIsNone(response)

    def test_middleware_empresa_attributes(self):
        """Test que middleware establece atributos correctos en request"""
        request = self.factory.get("/")
        request.session = {"empresa_id": self.empresa.id}
        request.user = self.user

        # Procesar request
        response = self.middleware.process_request(request)

        # Verificar atributos
        self.assertTrue(hasattr(request, "company"))
        self.assertTrue(hasattr(request, "country"))
        self.assertIsNone(response)

    def test_middleware_with_different_http_methods(self):
        """Test middleware con diferentes métodos HTTP"""
        # Test GET
        request = self.factory.get("/")
        request.session = {"empresa_id": self.empresa.id}
        request.user = self.user
        response = self.middleware.process_request(request)
        self.assertEqual(request.company, self.empresa)
        self.assertIsNone(response)

        # Test POST
        request = self.factory.post("/")
        request.session = {"empresa_id": self.empresa.id}
        request.user = self.user
        response = self.middleware.process_request(request)
        self.assertEqual(request.company, self.empresa)
        self.assertIsNone(response)
