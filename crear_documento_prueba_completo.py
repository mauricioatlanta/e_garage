#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings_sqlite')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from taller.models.documento import Documento, RepuestoDocumento, ServicioDocumento
from taller.models.empresa import Empresa
from taller.models.clientes import Cliente
from taller.models.vehiculos import Vehiculo
from taller.models.marca import Marca
from taller.models.modelo import Modelo
from taller.models.tecnico import Mecanico
from django.contrib.auth.models import User

print("=== CREAR DOCUMENTO DE PRUEBA COMPLETO ===")

# 1. Obtener usuario y empresa
user = User.objects.first()
empresa, _ = Empresa.objects.get_or_create(
    usuario=user,
    defaults={'nombre_taller': f'Taller de {user.username}'}
)

# 2. Obtener cliente
cliente = Cliente.objects.filter(empresa=empresa).first()

# 3. Obtener vehículo
vehiculo = Vehiculo.objects.filter(empresa=empresa).first()

# 4. Obtener mecánico
mecanico = Tecnico.objects.first()

print(f"✅ Usuario: {user.username}")
print(f"✅ Empresa: {empresa.nombre_taller}")
print(f"✅ Cliente: {cliente.nombre}")
print(f"✅ Vehículo: {vehiculo.patente}")
print(f"✅ Mecánico: {mecanico.nombre}")

# 5. Crear documento de prueba
documento = Documento.objects.create(
    empresa=empresa,
    tipo_documento="Orden de trabajo",
    numero_documento="NUEVO-TEST-001",
    cliente=cliente,
    vehiculo=vehiculo,
    mecanico=mecanico,
    kilometraje=95000,
    observaciones="Documento de prueba para las nuevas views - Con repuestos y servicios completos"
)

print(f"\n📄 Documento creado: {documento.numero_documento}")

# 6. Agregar repuestos de prueba
repuestos_data = [
    {"codigo": "FLT-001", "nombre": "Filtro de aceite Premium", "cantidad": 1, "precio": 18000},
    {"codigo": "ACE-5W30", "nombre": "Aceite motor 5W-30 sintético", "cantidad": 4, "precio": 12000},
    {"codigo": "BUJ-001", "nombre": "Bujías NGK platino", "cantidad": 4, "precio": 8500},
    {"codigo": "PAD-FRT", "nombre": "Pastillas freno delanteras", "cantidad": 1, "precio": 65000},
]

print(f"\n🔧 Creando repuestos:")
for i, rep_data in enumerate(repuestos_data, 1):
    repuesto = RepuestoDocumento.objects.create(
        documento=documento,
        codigo=rep_data["codigo"],
        nombre=rep_data["nombre"],
        cantidad=rep_data["cantidad"],
        precio=rep_data["precio"]
    )
    print(f"   {i}. {repuesto.nombre}: ${repuesto.precio} x {repuesto.cantidad} = ${repuesto.total}")

# 7. Agregar servicios de prueba
servicios_data = [
    {"nombre": "Cambio de aceite y filtro", "precio": 25000},
    {"nombre": "Cambio de bujías", "precio": 15000},
    {"nombre": "Cambio de pastillas de freno", "precio": 35000},
    {"nombre": "Revisión general", "precio": 20000},
    {"nombre": "Alineación y balanceo", "precio": 30000},
]

print(f"\n⚙️ Creando servicios:")
for i, serv_data in enumerate(servicios_data, 1):
    servicio = ServicioDocumento.objects.create(
        empresa=empresa,
        documento=documento,
        nombre=serv_data["nombre"],
        precio=serv_data["precio"]
    )
    print(f"   {i}. {servicio.nombre}: ${servicio.precio}")

# 8. Verificar totales
repuestos = RepuestoDocumento.objects.filter(documento=documento)
servicios = ServicioDocumento.objects.filter(documento=documento)

subtotal_repuestos = sum(r.total for r in repuestos)
subtotal_servicios = sum(s.precio for s in servicios)
subtotal = subtotal_repuestos + subtotal_servicios
iva = int(subtotal * 0.19)
total = subtotal + iva

print(f"\n💰 RESUMEN FINANCIERO:")
print(f"   Subtotal repuestos: ${subtotal_repuestos:,}")
print(f"   Subtotal servicios: ${subtotal_servicios:,}")
print(f"   Subtotal: ${subtotal:,}")
print(f"   IVA (19%): ${iva:,}")
print(f"   TOTAL: ${total:,}")

print(f"\n🎯 URLS PARA PROBAR:")
print(f"   Ver documento nuevo: http://127.0.0.1:8000/documentos/nuevo-ver/{documento.id}/")
print(f"   Editar documento nuevo: http://127.0.0.1:8000/documentos/nuevo-editar/{documento.id}/")
print(f"   Test de datos: http://127.0.0.1:8000/documentos/test-datos/{documento.id}/")

print(f"\n✅ Documento de prueba completo creado exitosamente")
print(f"📋 Contiene {repuestos.count()} repuestos y {servicios.count()} servicios")
print(f"🆔 ID del documento: {documento.id}")
