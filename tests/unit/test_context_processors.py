"""
Tests para context processors - cobertura rápida de procesadores de contexto
"""
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import AnonymousUser

from taller.context_processors import empresa_contexto
from taller.models.empresa import Empresa


class ContextProcessorsTest(TestCase):
    """Tests para context processors"""
    
    def setUp(self):
        """Setup básico para tests"""
        from django.contrib.auth.models import User
        
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )
        self.empresa = Empresa.objects.create(
            nombre_taller="Test Garage",
            pais="CL",
            user=self.user
        )

    def test_empresa_contexto_with_empresa(self):
        """Test context processor con empresa en request"""
        request = self.factory.get('/')
        request.empresa = self.empresa
        
        context = empresa_contexto(request)
        
        # Verificar que retorna el contexto esperado
        self.assertIn('empresa_actual', context)
        self.assertIn('empresa', context)
        self.assertIn('nombre_taller', context)
        # Como no hay configuración, debería ser None
        self.assertIsNone(context['empresa_actual'])
        self.assertIsNone(context['empresa'])

    def test_empresa_contexto_without_empresa(self):
        """Test context processor sin empresa en request"""
        request = self.factory.get('/')
        # No establecer request.empresa
        
        context = empresa_contexto(request)
        
        # Verificar que retorna el contexto esperado
        self.assertIn('empresa_actual', context)
        self.assertIsNone(context['empresa_actual'])

    def test_empresa_contexto_with_none_empresa(self):
        """Test context processor con empresa None en request"""
        request = self.factory.get('/')
        request.empresa = None
        
        context = empresa_contexto(request)
        
        # Verificar que retorna el contexto esperado
        self.assertIn('empresa_actual', context)
        self.assertIsNone(context['empresa_actual'])

    def test_empresa_contexto_empresa_without_configuracion(self):
        """Test context processor con empresa sin configuración"""
        request = self.factory.get('/')
        request.empresa = self.empresa
        
        # Verificar que la empresa no tiene configuración
        self.assertFalse(hasattr(self.empresa, 'configuracionempresa'))
        
        context = empresa_contexto(request)
        
        # Verificar que retorna el contexto esperado
        self.assertIn('empresa_actual', context)
        self.assertIsNone(context['empresa_actual'])

    def test_empresa_contexto_return_type(self):
        """Test que el context processor retorna un diccionario"""
        request = self.factory.get('/')
        request.empresa = self.empresa

        context = empresa_contexto(request)

        # Verificar que retorna un diccionario
        self.assertIsInstance(context, dict)
        self.assertGreaterEqual(len(context), 1)  # Debe tener al menos 1 elemento

    def test_empresa_contexto_key_exists(self):
        """Test que el context processor siempre incluye la clave empresa_actual"""
        request = self.factory.get('/')
        
        context = empresa_contexto(request)
        
        # Verificar que siempre incluye la clave
        self.assertIn('empresa_actual', context)

    def test_empresa_contexto_with_different_request_methods(self):
        """Test context processor con diferentes métodos HTTP"""
        # Test GET
        request = self.factory.get('/')
        request.empresa = self.empresa
        context = empresa_contexto(request)
        self.assertIn('empresa_actual', context)
        
        # Test POST
        request = self.factory.post('/')
        request.empresa = self.empresa
        context = empresa_contexto(request)
        self.assertIn('empresa_actual', context)
        
        # Test PUT
        request = self.factory.put('/')
        request.empresa = self.empresa
        context = empresa_contexto(request)
        self.assertIn('empresa_actual', context)

    def test_empresa_contexto_with_authenticated_user(self):
        """Test context processor con usuario autenticado"""
        from django.contrib.auth.models import User
        
        user = User.objects.create_user(
            username='testuser2',
            password='testpass'
        )
        
        request = self.factory.get('/')
        request.user = user
        request.empresa = self.empresa
        
        context = empresa_contexto(request)
        
        # Verificar que funciona independientemente del usuario
        self.assertIn('empresa_actual', context)
        self.assertIsNone(context['empresa_actual'])

    def test_empresa_contexto_with_anonymous_user(self):
        """Test context processor con usuario anónimo"""
        request = self.factory.get('/')
        request.user = AnonymousUser()
        request.empresa = self.empresa
        
        context = empresa_contexto(request)
        
        # Verificar que funciona con usuario anónimo
        self.assertIn('empresa_actual', context)
        self.assertIsNone(context['empresa_actual'])

    def test_empresa_contexto_empresa_attribute_access(self):
        """Test que el context processor maneja correctamente el acceso a atributos"""
        request = self.factory.get('/')
        
        # Crear un objeto mock que simule una empresa sin configuracionempresa
        class MockEmpresa:
            def __init__(self):
                self.id = 1
                self.nombre_taller = "Mock Garage"
        
        mock_empresa = MockEmpresa()
        request.empresa = mock_empresa
        
        context = empresa_contexto(request)
        
        # Verificar que maneja correctamente la falta del atributo
        # El context processor real retorna diferentes claves
        self.assertIn('empresa_actual', context)
        self.assertIn('empresa', context)
        self.assertIn('nombre_taller', context)
        self.assertIsNone(context['empresa_actual'])
        self.assertIsNone(context['empresa'])
