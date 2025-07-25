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
from taller.models.mecanico import Mecanico
from django.contrib.auth.models import User
import json

print("=== TEST CREAR DOCUMENTO CON REPUESTOS/SERVICIOS ===")

# 1. Obtener o crear usuario y empresa
user = User.objects.first()
if not user:
    print("❌ No hay usuarios en la base de datos")
    sys.exit(1)

empresa, created = Empresa.objects.get_or_create(
    usuario=user,
    defaults={'nombre_taller': f'Taller de {user.username}'}
)
print(f"🏢 Empresa: {empresa.nombre_taller} ({'creada' if created else 'existente'})")

# 2. Obtener o crear cliente
cliente = Cliente.objects.first()
if not cliente:
    cliente = Cliente.objects.create(
        empresa=empresa,
        nombre="Cliente Prueba",
        email="test@test.com",
        telefono="123456789"
    )
print(f"👤 Cliente: {cliente.nombre}")

# 3. Obtener o crear vehículo
vehiculo = Vehiculo.objects.filter(empresa=empresa).first()
if not vehiculo:
    from taller.models.marca import Marca
    from taller.models.modelo import Modelo
    
    marca, _ = Marca.objects.get_or_create(nombre="Toyota")
    modelo, _ = Modelo.objects.get_or_create(marca=marca, nombre="Corolla")
    
    vehiculo = Vehiculo.objects.create(
        empresa=empresa,
        cliente=cliente,
        marca=marca,
        modelo=modelo,
        patente="ABC123",
        anio=2020
    )
print(f"🚗 Vehículo: {vehiculo.patente}")

# 4. Obtener o crear mecánico
mecanico, _ = Mecanico.objects.get_or_create(nombre="Mecánico Prueba")
print(f"🔧 Mecánico: {mecanico.nombre}")

# 5. Crear documento
documento = Documento.objects.create(
    empresa=empresa,
    tipo_documento="Presupuesto",
    numero_documento="TEST-00001",
    cliente=cliente,
    vehiculo=vehiculo,
    mecanico=mecanico,
    kilometraje=50000,
    observaciones="Documento de prueba"
)
print(f"📄 Documento creado: {documento.numero_documento}")

# 6. Agregar repuestos
print("\n🔧 Creando repuestos...")
repuesto1 = RepuestoDocumento.objects.create(
    documento=documento,
    codigo="REP001",
    nombre="Filtro de aceite",
    cantidad=1,
    precio=15000
)

repuesto2 = RepuestoDocumento.objects.create(
    documento=documento,
    codigo="REP002", 
    nombre="Pastillas de freno",
    cantidad=2,
    precio=45000
)

print(f"   ✅ {repuesto1.nombre}: ${repuesto1.precio} x {repuesto1.cantidad}")
print(f"   ✅ {repuesto2.nombre}: ${repuesto2.precio} x {repuesto2.cantidad}")

# 7. Agregar servicios
print("\n⚙️ Creando servicios...")
servicio1 = ServicioDocumento.objects.create(
    empresa=empresa,
    documento=documento,
    nombre="Cambio de aceite",
    precio=25000
)

servicio2 = ServicioDocumento.objects.create(
    empresa=empresa,
    documento=documento,
    nombre="Alineación",
    precio=35000
)

print(f"   ✅ {servicio1.nombre}: ${servicio1.precio}")
print(f"   ✅ {servicio2.nombre}: ${servicio2.precio}")

# 8. Verificar que se guardaron correctamente
print("\n📊 VERIFICACIÓN:")
repuestos_encontrados = RepuestoDocumento.objects.filter(documento=documento)
servicios_encontrados = ServicioDocumento.objects.filter(documento=documento)

print(f"   Repuestos en BD: {repuestos_encontrados.count()}")
for rep in repuestos_encontrados:
    print(f"     - {rep.nombre}: ${rep.precio} x {rep.cantidad} = ${rep.total}")

print(f"   Servicios en BD: {servicios_encontrados.count()}")
for serv in servicios_encontrados:
    print(f"     - {serv.nombre}: ${serv.precio}")

# 9. Simular lo que hace la view ver_documento
print(f"\n🔍 SIMULANDO VIEW VER_DOCUMENTO:")
print(f"   Usuario: {user.username}")
print(f"   Empresa del usuario: {empresa.nombre_taller}")
print(f"   Documento ID: {documento.id}")

# Simular filtrado por empresa como en la view
documento_filtrado = Documento.objects.filter(id=documento.id, empresa=empresa).first()
if documento_filtrado:
    print(f"   ✅ Documento encontrado con filtro de empresa")
    repuestos_view = RepuestoDocumento.objects.filter(documento=documento_filtrado)
    servicios_view = ServicioDocumento.objects.filter(documento=documento_filtrado)
    print(f"   ✅ Repuestos desde view: {repuestos_view.count()}")
    print(f"   ✅ Servicios desde view: {servicios_view.count()}")
else:
    print(f"   ❌ Documento NO encontrado con filtro de empresa")

print(f"\n✅ Documento de prueba creado exitosamente: ID {documento.id}")
