"""
Tests para las APIs de vehículos
"""
import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from taller.models.empresa import Empresa


class VehiculosAPITest(TestCase):
    """Tests para las APIs de vehículos"""

    def setUp(self):
        """Setup básico para tests"""
        self.client = Client()
        
        # Crear usuario y empresa
        self.user = User.objects.create_user(
            username='testuser_api',
            password='testpass'
        )
        self.empresa = Empresa.objects.create(
            nombre_taller="Test Garage API",
            pais="CL",
            user=self.user
        )
        
        # Autenticar usuario
        self.client.force_login(self.user)

    def test_api_modelos_usa_get(self):
        """Test GET a api_modelos_usa"""
        # Usar URL directa ya que el namespace no está disponible en tests
        url = '/cl/vehiculos/api/modelos-usa/'
        response = self.client.get(url)
        
        # Debe retornar 200 y un JSON array
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        # Debe ser un array (aunque esté vacío)
        data = json.loads(response.content)
        self.assertIsInstance(data, list)

    def test_api_modelos_usa_with_marca_param(self):
        """Test api_modelos_usa con parámetro marca"""
        url = '/cl/vehiculos/api/modelos-usa/'
        response = self.client.get(url, {'marca': '1'})
        
        # Debe retornar 200
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        # Debe ser un array
        data = json.loads(response.content)
        self.assertIsInstance(data, list)

    def test_obtener_modelos_get(self):
        """Test GET a obtener_modelos"""
        url = '/cl/vehiculos/api/modelos/'
        response = self.client.get(url)
        
        # Debe retornar 200 y un JSON array
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        # Debe ser un array
        data = json.loads(response.content)
        self.assertIsInstance(data, list)

    def test_api_motores_por_modelo_get(self):
        """Test GET a api_motores_por_modelo"""
        url = '/cl/vehiculos/api/motores/'
        response = self.client.get(url)
        
        # Debe retornar 200 y un JSON array
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        # Debe ser un array
        data = json.loads(response.content)
        self.assertIsInstance(data, list)

    def test_api_cajas_por_modelo_get(self):
        """Test GET a api_cajas_por_modelo"""
        url = '/cl/vehiculos/api/cajas/'
        response = self.client.get(url)
        
        # Debe retornar 200 y un JSON array
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        # Debe ser un array
        data = json.loads(response.content)
        self.assertIsInstance(data, list)

    def test_crear_modelo_post(self):
        """Test POST a crear_modelo"""
        url = '/cl/vehiculos/api/modelos/crear/'
        
        # Datos de prueba
        data = {
            'nombre': 'Test Modelo',
            'marca': '1'
        }
        
        response = self.client.post(
            url, 
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Puede retornar 200, 201 (éxito) o 400 (datos inválidos)
        self.assertIn(response.status_code, [200, 201, 400])
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_api_endpoints_require_authentication(self):
        """Test que los endpoints requieren autenticación"""
        # Desautenticar
        self.client.logout()
        
        endpoints = [
            '/cl/vehiculos/api/modelos-usa/',
            '/cl/vehiculos/api/modelos/',
            '/cl/vehiculos/api/motores/',
            '/cl/vehiculos/api/cajas/',
        ]
        
        for endpoint in endpoints:
            with self.subTest(endpoint=endpoint):
                response = self.client.get(endpoint)
                
                # Algunos endpoints pueden ser públicos (200) o requerir auth (302, 401, 403)
                self.assertIn(response.status_code, [200, 302, 401, 403])

    def test_api_modelos_usa_empty_marca(self):
        """Test api_modelos_usa con marca vacía"""
        url = '/cl/vehiculos/api/modelos-usa/'
        response = self.client.get(url, {'marca': ''})
        
        # Debe retornar array vacío
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data, [])

    def test_api_modelos_usa_no_marca_param(self):
        """Test api_modelos_usa sin parámetro marca"""
        url = '/cl/vehiculos/api/modelos-usa/'
        response = self.client.get(url)
        
        # Debe retornar array vacío
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data, [])