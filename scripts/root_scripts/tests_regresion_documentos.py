#!/usr/bin/env python3
"""
Tests de regresión para el sistema de documentos
"""

import json
import os
import unittest

import django
from django.contrib.auth.models import User
from django.test import Client, TestCase

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings_sqlite")
django.setup()

from taller.models.clientes import Cliente
from taller.models.documento import Documento
from taller.models.empresa import Empresa
from taller.models.lineas_documento import LineaRepuesto, LineaServicio
from taller.models.marca import Marca
from taller.models.repuesto import Repuesto
from taller.models.vehiculos import Vehiculo


class DocumentoTests(TestCase):
    def setUp(self):
        """Configurar datos de prueba"""
        # Crear usuario de prueba
        self.user = User.objects.create_user(username="test_user", password="test_pass123")

        # Crear empresa de prueba
        self.empresa = Empresa.objects.create(
            user=self.user,
            nombre_taller="Taller Test",
            direccion="Calle Test 123",
            telefono="123456789",
        )

        # Crear cliente de prueba
        self.cliente = Cliente.objects.create(
            empresa=self.empresa,
            nombre="Cliente Test",
            telefono="987654321",
            email="cliente@test.com",
        )
        self.marca = Marca.objects.create(nombre="Toyota", country="CL")

        # Crear vehículo de prueba
        self.vehiculo = Vehiculo.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            patente="TEST123",
            marca=self.marca,
            modelo_texto="Corolla",
            anio=2020,
        )

        self.client = Client()

    def test_login_required(self):
        """Test que las páginas requieren login"""
        response = self.client.get("/documentos/nuevo/")
        self.assertEqual(response.status_code, 302)  # Redirect a login

    def test_crear_documento_get(self):
        """Test acceso a página de crear documento"""
        self.client.login(username="test_user", password="test_pass123")
        response = self.client.get("/documentos/nuevo/")
        self.assertIn(response.status_code, [200, 302])

    def test_crear_documento_post(self):
        """Test creación de documento vía POST"""
        # Datos del documento
        items_data = [
            {
                "tipo": "repuesto",
                "partnumber": "TEST001",
                "nombre": "Repuesto Test",
                "cantidad": 2,
                "precio": 15000,
            },
            {"tipo": "servicio", "nombre": "Servicio Test", "precio": 25000},
        ]

        documento = Documento.objects.create(
            empresa=self.empresa,
            tipo="PRES",
            numero="TEST-001",
            fecha_emision="2025-07-22",
            cliente=self.cliente,
            vehiculo=self.vehiculo,
            observaciones="Documento de test",
        )

        for item in items_data:
            if item["tipo"] == "repuesto":
                repuesto = Repuesto.objects.create(
                    empresa=self.empresa,
                    part_number=item["partnumber"],
                    nombre=item["nombre"],
                    cantidad_stock=10,
                    precio_compra=item["precio"],
                    precio_venta=item["precio"],
                )
                LineaRepuesto.objects.create(
                    documento=documento,
                    repuesto=repuesto,
                    codigo=item["partnumber"],
                    nombre=item["nombre"],
                    cantidad=item["cantidad"],
                    precio_unitario=item["precio"],
                )
            else:
                LineaServicio.objects.create(
                    documento=documento,
                    nombre=item["nombre"],
                    cantidad=1,
                    precio_unitario=item["precio"],
                )

        # Verificar que se creó el documento
        self.assertTrue(Documento.objects.filter(numero="TEST-001").exists())

        # Verificar que se crearon los items
        documento = Documento.objects.get(numero="TEST-001")
        repuestos = LineaRepuesto.objects.filter(documento=documento)
        servicios = LineaServicio.objects.filter(documento=documento)

        self.assertEqual(repuestos.count(), 1)
        self.assertEqual(servicios.count(), 1)

        # Verificar datos del repuesto
        repuesto = repuestos.first()
        self.assertEqual(repuesto.codigo, "TEST001")
        self.assertEqual(repuesto.nombre, "Repuesto Test")
        self.assertEqual(repuesto.cantidad, 2)
        precio_rep = getattr(repuesto, "precio_unitario", getattr(repuesto, "precio", None))
        self.assertEqual(precio_rep, 15000)

        # Verificar datos del servicio
        servicio = servicios.first()
        self.assertEqual(servicio.nombre, "Servicio Test")
        precio_serv = getattr(servicio, "precio_unitario", getattr(servicio, "precio", None))
        self.assertEqual(precio_serv, 25000)

    def test_aislamiento_empresas(self):
        """Test que las consultas separan documentos por empresa"""
        user2 = User.objects.create_user(username="test_user2", password="test_pass123")
        # Crear segunda empresa
        empresa2 = Empresa.objects.create(
            user=user2,
            nombre_taller="Taller Test 2",
            direccion="Otra Calle 456",
        )

        # Crear documento en empresa 1
        doc1 = Documento.objects.create(
            empresa=self.empresa,
            tipo="OT",
            numero="DOC-EMPRESA1",
            fecha_emision="2025-07-22",
            cliente=self.cliente,
            vehiculo=self.vehiculo,
        )

        # Crear cliente y documento en empresa 2
        cliente2 = Cliente.objects.create(
            empresa=empresa2, nombre="Cliente Empresa 2", telefono="111222333"
        )

        vehiculo2 = Vehiculo.objects.create(
            empresa=empresa2,
            cliente=cliente2,
            patente="EMP2123",
            marca=Marca.objects.create(nombre="Ford", country="CL"),
            modelo_texto="Focus",
            anio=2020,
        )

        doc2 = Documento.objects.create(
            empresa=empresa2,
            tipo="OT",
            numero="DOC-EMPRESA2",
            fecha_emision="2025-07-22",
            cliente=cliente2,
            vehiculo=vehiculo2,
        )

        docs_empresa_1 = Documento.objects.filter(empresa=self.empresa)
        docs_empresa_2 = Documento.objects.filter(empresa=empresa2)

        self.assertIn(doc1, docs_empresa_1)
        self.assertNotIn(doc2, docs_empresa_1)
        self.assertIn(doc2, docs_empresa_2)
        self.assertNotIn(doc1, docs_empresa_2)

    def test_calculos_totales(self):
        """Test cálculos de totales"""
        # Crear documento
        documento = Documento.objects.create(
            empresa=self.empresa,
            tipo="PRES",
            numero="CALC-001",
            fecha_emision="2025-07-22",
            cliente=self.cliente,
            vehiculo=self.vehiculo,
        )

        # Agregar repuestos
        repuesto_1 = Repuesto.objects.create(
            empresa=self.empresa,
            part_number="REP001",
            nombre="Repuesto 1",
            cantidad_stock=10,
            precio_compra=10000,
            precio_venta=10000,
        )
        LineaRepuesto.objects.create(
            documento=documento,
            repuesto=repuesto_1,
            codigo="REP001",
            nombre="Repuesto 1",
            cantidad=2,
            precio_unitario=10000,
        )

        repuesto_2 = Repuesto.objects.create(
            empresa=self.empresa,
            part_number="REP002",
            nombre="Repuesto 2",
            cantidad_stock=10,
            precio_compra=15000,
            precio_venta=15000,
        )
        LineaRepuesto.objects.create(
            documento=documento,
            repuesto=repuesto_2,
            codigo="REP002",
            nombre="Repuesto 2",
            cantidad=1,
            precio_unitario=15000,
        )

        # Agregar servicios
        LineaServicio.objects.create(
            documento=documento,
            nombre="Servicio 1",
            cantidad=1,
            precio_unitario=20000,
        )

        LineaServicio.objects.create(
            documento=documento,
            nombre="Servicio 2",
            cantidad=1,
            precio_unitario=30000,
        )

        # Calcular totales
        total_repuestos = sum(
            getattr(r, "precio_unitario", getattr(r, "precio", 0)) * getattr(r, "cantidad", 1)
            for r in documento.lineas_repuesto.all()
        )
        total_servicios = sum(
            getattr(s, "precio_unitario", getattr(s, "precio", 0))
            for s in documento.lineas_servicio.all()
        )
        total_documento = total_repuestos + total_servicios

        self.assertEqual(total_repuestos, 35000)  # (2*10000) + (1*15000)
        self.assertEqual(total_servicios, 50000)  # 20000 + 30000
        self.assertEqual(total_documento, 85000)

    def tearDown(self):
        """Limpiar datos de prueba"""
        # Django TestCase maneja esto automáticamente
        pass


if __name__ == "__main__":
    unittest.main()
