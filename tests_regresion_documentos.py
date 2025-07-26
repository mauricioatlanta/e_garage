#!/usr/bin/env python3
"""
Tests de regresión para el sistema de documentos
"""
import os
import django
import unittest
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings_sqlite')
django.setup()

from taller.models.perfil_usuario import PerfilUsuario
from taller.models.empresa import Empresa
from taller.models.documento import Documento, RepuestoDocumento, ServicioDocumento
from taller.models.cliente import Cliente
from taller.models.vehiculo import Vehiculo


class DocumentoTests(TestCase):
    def setUp(self):
        """Configurar datos de prueba"""
        # Crear empresa de prueba
        self.empresa = Empresa.objects.create(
            nombre_taller="Taller Test",
            direccion="Calle Test 123",
            telefono="123456789"
        )
        
        # Crear usuario de prueba
        self.user = User.objects.create_user(
            username='test_user',
            password='test_pass123'
        )
        
        # Crear perfil de usuario
        self.perfil = PerfilUsuario.objects.create(
            user=self.user,
            empresa=self.empresa,
            rol='admin'
        )
        
        # Crear cliente de prueba
        self.cliente = Cliente.objects.create(
            empresa=self.empresa,
            nombre="Cliente Test",
            telefono="987654321",
            email="cliente@test.com"
        )
        
        # Crear vehículo de prueba
        self.vehiculo = Vehiculo.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            patente="TEST123",
            marca="Toyota",
            modelo="Corolla",
            año=2020
        )
        
        self.client = Client()
    
    def test_login_required(self):
        """Test que las páginas requieren login"""
        response = self.client.get('/documentos/nuevo/')
        self.assertEqual(response.status_code, 302)  # Redirect a login
    
    def test_crear_documento_get(self):
        """Test acceso a página de crear documento"""
        self.client.login(username='test_user', password='test_pass123')
        response = self.client.get('/documentos/nuevo/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Crear Documento')
    
    def test_crear_documento_post(self):
        """Test creación de documento vía POST"""
        self.client.login(username='test_user', password='test_pass123')
        
        # Datos del documento
        items_data = [
            {
                "tipo": "repuesto",
                "partnumber": "TEST001",
                "nombre": "Repuesto Test",
                "cantidad": 2,
                "precio": 15000
            },
            {
                "tipo": "servicio",
                "nombre": "Servicio Test",
                "precio": 25000
            }
        ]
        
        data = {
            'tipo_documento': 'Presupuesto',
            'numero_documento': 'TEST-001',
            'fecha': '2025-07-22',
            'cliente': self.cliente.id,
            'vehiculo': self.vehiculo.id,
            'observaciones': 'Documento de test',
            'json_items': json.dumps(items_data)
        }
        
        response = self.client.post('/documentos/nuevo/', data)
        
        # Verificar que se creó el documento
        self.assertTrue(Documento.objects.filter(numero_documento='TEST-001').exists())
        
        # Verificar que se crearon los items
        documento = Documento.objects.get(numero_documento='TEST-001')
        repuestos = RepuestoDocumento.objects.filter(documento=documento)
        servicios = ServicioDocumento.objects.filter(documento=documento)
        
        self.assertEqual(repuestos.count(), 1)
        self.assertEqual(servicios.count(), 1)
        
        # Verificar datos del repuesto
        repuesto = repuestos.first()
        self.assertEqual(repuesto.codigo, 'TEST001')
        self.assertEqual(repuesto.nombre, 'Repuesto Test')
        self.assertEqual(repuesto.cantidad, 2)
        self.assertEqual(repuesto.precio, 15000)
        
        # Verificar datos del servicio
        servicio = servicios.first()
        self.assertEqual(servicio.nombre, 'Servicio Test')
        self.assertEqual(servicio.precio, 25000)
    
    def test_aislamiento_empresas(self):
        """Test que las empresas no ven documentos de otras"""
        # Crear segunda empresa
        empresa2 = Empresa.objects.create(
            nombre_taller="Taller Test 2",
            direccion="Otra Calle 456"
        )
        
        user2 = User.objects.create_user(
            username='test_user2',
            password='test_pass123'
        )
        
        PerfilUsuario.objects.create(
            user=user2,
            empresa=empresa2,
            rol='admin'
        )
        
        # Crear documento en empresa 1
        doc1 = Documento.objects.create(
            empresa=self.empresa,
            numero_documento='DOC-EMPRESA1',
            fecha='2025-07-22',
            cliente=self.cliente,
            vehiculo=self.vehiculo
        )
        
        # Crear cliente y documento en empresa 2
        cliente2 = Cliente.objects.create(
            empresa=empresa2,
            nombre="Cliente Empresa 2",
            telefono="111222333"
        )
        
        vehiculo2 = Vehiculo.objects.create(
            empresa=empresa2,
            cliente=cliente2,
            patente="EMP2123",
            marca="Ford",
            modelo="Focus"
        )
        
        doc2 = Documento.objects.create(
            empresa=empresa2,
            numero_documento='DOC-EMPRESA2',
            fecha='2025-07-22',
            cliente=cliente2,
            vehiculo=vehiculo2
        )
        
        # Login como usuario 1 y verificar que solo ve sus documentos
        self.client.login(username='test_user', password='test_pass123')
        response = self.client.get('/documentos/')
        
        self.assertContains(response, 'DOC-EMPRESA1')
        self.assertNotContains(response, 'DOC-EMPRESA2')
        
        # Login como usuario 2 y verificar lo mismo
        self.client.login(username='test_user2', password='test_pass123')
        response = self.client.get('/documentos/')
        
        self.assertContains(response, 'DOC-EMPRESA2')
        self.assertNotContains(response, 'DOC-EMPRESA1')
    
    def test_calculos_totales(self):
        """Test cálculos de totales"""
        # Crear documento
        documento = Documento.objects.create(
            empresa=self.empresa,
            numero_documento='CALC-001',
            fecha='2025-07-22',
            cliente=self.cliente,
            vehiculo=self.vehiculo
        )
        
        # Agregar repuestos
        RepuestoDocumento.objects.create(
            documento=documento,
            codigo='REP001',
            nombre='Repuesto 1',
            cantidad=2,
            precio=10000
        )
        
        RepuestoDocumento.objects.create(
            documento=documento,
            codigo='REP002',
            nombre='Repuesto 2',
            cantidad=1,
            precio=15000
        )
        
        # Agregar servicios
        ServicioDocumento.objects.create(
            empresa=self.empresa,
            documento=documento,
            nombre='Servicio 1',
            precio=20000
        )
        
        ServicioDocumento.objects.create(
            empresa=self.empresa,
            documento=documento,
            nombre='Servicio 2',
            precio=30000
        )
        
        # Calcular totales
        total_repuestos = sum(r.total for r in documento.repuestodocumento_set.all())
        total_servicios = sum(s.precio for s in documento.serviciodocumento_set.all())
        total_documento = total_repuestos + total_servicios
        
        self.assertEqual(total_repuestos, 35000)  # (2*10000) + (1*15000)
        self.assertEqual(total_servicios, 50000)  # 20000 + 30000
        self.assertEqual(total_documento, 85000)
    
    def tearDown(self):
        """Limpiar datos de prueba"""
        # Django TestCase maneja esto automáticamente
        pass


if __name__ == '__main__':
    unittest.main()
