#!/usr/bin/env python
"""
🎯 CREADOR DE DATOS DE PRUEBA PARA REPORTES AVANZADOS
==================================================

Script para crear servicios subcontratados de ejemplo y probar los nuevos reportes
"""

import os
import django
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from taller.models.documento import Documento, OtroServicioDocumento
from taller.models.clientes import Cliente
from taller.models.vehiculos import Vehiculo
from taller.models.empresa import Empresa
from datetime import date, timedelta
import random

def crear_datos_prueba():
    """Crear datos de prueba para servicios subcontratados"""
    
    print("🚀 Creando datos de prueba para reportes avanzados...")
    
    # Obtener empresa activa
    try:
        empresa = Empresa.objects.first()
        if not empresa:
            print("❌ No hay empresas registradas")
            return
    except Exception as e:
        print(f"❌ Error obteniendo empresa: {e}")
        return
    
    # Servicios externos de ejemplo
    servicios_externos = [
        {"nombre": "Alineación y Balanceo", "proveedor": "AutoCenter Express", "costo_base": 25000, "precio_base": 35000},
        {"nombre": "Cambio de Aceite Premium", "proveedor": "Lubricantes ProMax", "costo_base": 45000, "precio_base": 65000},
        {"nombre": "Reparación de Transmisión", "proveedor": "TransmisionTech", "costo_base": 150000, "precio_base": 200000},
        {"nombre": "Diagnóstico Computarizado", "proveedor": "DiagnosticPro", "costo_base": 35000, "precio_base": 50000},
        {"nombre": "Instalación de Audio", "proveedor": "SoundCar", "costo_base": 80000, "precio_base": 120000},
        {"nombre": "Pintura Completa", "proveedor": "PaintMaster", "costo_base": 400000, "precio_base": 550000},
        {"nombre": "Cambio de Llantas", "proveedor": "Llantas Express", "costo_base": 180000, "precio_base": 220000},
        {"nombre": "Reparación de Motor", "proveedor": "MotorTech Expert", "costo_base": 300000, "precio_base": 420000},
        {"nombre": "Aire Acondicionado", "proveedor": "ClimaCar", "costo_base": 90000, "precio_base": 130000},
        {"nombre": "Sistema Eléctrico", "proveedor": "ElectroCar", "costo_base": 75000, "precio_base": 105000},
    ]
    
    # Obtener algunos clientes existentes
    clientes = list(Cliente.objects.all()[:10])
    if not clientes:
        print("❌ No hay clientes registrados")
        return
    
    # Obtener algunos vehículos existentes
    vehiculos = list(Vehiculo.objects.all()[:10])
    if not vehiculos:
        print("❌ No hay vehículos registrados")
        return
    
    # Crear documentos de factura con servicios externos
    documentos_creados = 0
    servicios_creados = 0
    
    for i in range(30):  # Crear 30 documentos de ejemplo
        try:
            # Fecha aleatoria en los últimos 6 meses
            fecha_base = date.today() - timedelta(days=180)
            fecha_random = fecha_base + timedelta(days=random.randint(0, 180))
            
            # Crear documento
            documento = Documento.objects.create(
                empresa=empresa,
                tipo_documento='Factura',
                numero_documento=f'FACT-EXT-{1000 + i}',
                fecha=fecha_random,
                cliente=random.choice(clientes),
                vehiculo=random.choice(vehiculos),
                kilometraje=random.randint(50000, 200000),
                observaciones=f'Factura con servicios subcontratados - {i+1}',
                incluir_iva=True
            )
            documentos_creados += 1
            
            # Agregar 1-3 servicios externos aleatorios al documento
            num_servicios = random.randint(1, 3)
            servicios_elegidos = random.sample(servicios_externos, num_servicios)
            
            for servicio in servicios_elegidos:
                # Variación de precios ±20%
                variacion = random.uniform(0.8, 1.2)
                costo_final = int(servicio['costo_base'] * variacion)
                precio_final = int(servicio['precio_base'] * variacion)
                
                # Crear servicio externo
                OtroServicioDocumento.objects.create(
                    documento=documento,
                    nombre_servicio=servicio['nombre'],
                    empresa_externa=servicio['proveedor'],
                    costo_interno=costo_final,
                    precio_cliente=precio_final,
                    observaciones=f'Servicio realizado por {servicio["proveedor"]}'
                )
                servicios_creados += 1
                
        except Exception as e:
            print(f"❌ Error creando documento {i}: {e}")
            continue
    
    print(f"✅ Datos de prueba creados:")
    print(f"   📄 Documentos: {documentos_creados}")
    print(f"   🔧 Servicios externos: {servicios_creados}")
    print(f"   🏢 Proveedores únicos: {len(servicios_externos)}")
    
    # Mostrar estadísticas
    total_servicios = OtroServicioDocumento.objects.count()
    total_ingresos = sum([s.precio_cliente for s in OtroServicioDocumento.objects.all()])
    total_costos = sum([s.costo_interno for s in OtroServicioDocumento.objects.all()])
    ganancia_total = total_ingresos - total_costos
    
    print(f"\n📊 Estadísticas generales:")
    print(f"   💰 Total ingresos: ${total_ingresos:,}")
    print(f"   💸 Total costos: ${total_costos:,}")
    print(f"   📈 Ganancia total: ${ganancia_total:,}")
    print(f"   📊 Margen promedio: {(ganancia_total/total_ingresos*100):.1f}%")
    
    print(f"\n🎯 Reportes disponibles en:")
    print(f"   🌐 http://127.0.0.1:8001/reportes/")
    print(f"   📈 http://127.0.0.1:8001/reportes/dashboard-rentabilidad/")

if __name__ == "__main__":
    crear_datos_prueba()
