#!/usr/bin/env python
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from taller.documentos.models import Documento, LineaServicio
from taller.servicios.models import Servicio
from taller.models import Empresa
from decimal import Decimal

print("=== AGREGANDO SERVICIOS A DOCUMENTOS ===")

# Buscar empresa USA
try:
    empresa = Empresa.objects.get(nombre_taller='USA Test Garage')
    print(f"✅ Empresa encontrada: {empresa.nombre_taller}")
except Empresa.DoesNotExist:
    print("❌ No se encontró la empresa 'USA Test Garage'")
    exit(1)

# Verificar documentos
docs = Documento.objects.filter(empresa=empresa).order_by('id')
print(f"📄 Documentos encontrados: {docs.count()}")

# Verificar servicios disponibles
servicios = Servicio.objects.filter(empresa=empresa)
print(f"🔧 Servicios disponibles: {servicios.count()}")

if servicios.count() == 0:
    print("⚠️ No hay servicios disponibles. Usando servicios externos...")
    
    # Usar servicios externos que sí tienen precios
    from taller.servicios.models import ServicioExterno
    servicios = ServicioExterno.objects.filter(empresa=empresa)
    print(f"🔧 Servicios externos disponibles: {servicios.count()}")
    
    if servicios.count() == 0:
        print("❌ No hay servicios externos disponibles tampoco")
        exit(1)

print(f"\n🔧 Servicios disponibles para usar:")
for servicio in servicios[:4]:
    precio = getattr(servicio, 'precio_cliente', getattr(servicio, 'precio_base', 'N/A'))
    print(f"   - {servicio.nombre}: ${precio}")

# Agregar servicios a cada documento
for i, doc in enumerate(docs):
    print(f"\n--- Documento {doc.pk} ({doc.tipo}) ---")
    
    # Verificar servicios existentes
    servicios_existentes = LineaServicio.objects.filter(documento=doc)
    print(f"🔧 Servicios actuales: {servicios_existentes.count()}")
    
    # Si no tiene servicios, agregar uno
    if servicios_existentes.count() == 0:
        # Usar servicio rotativo según el índice del documento
        servicio_index = i % servicios.count()
        servicio = servicios[servicio_index]
        
        # Determinar precio según tipo de servicio
        precio = getattr(servicio, 'precio_cliente', getattr(servicio, 'precio_base', Decimal('50.00')))
        
        try:
            linea_servicio = LineaServicio.objects.create(
                documento=doc,
                servicio=servicio if hasattr(servicio, 'categoria') else None,
                nombre=servicio.nombre,
                cantidad=Decimal('1'),
                precio_unitario=precio,
                descuento=Decimal('0'),
                observaciones=f"Servicio agregado automáticamente"
            )
            print(f"✅ Servicio agregado: {linea_servicio.nombre} - ${linea_servicio.precio_unitario}")
            
            # Actualizar totales del documento
            doc.neto_servicios = linea_servicio.precio_unitario
            total_anterior = doc.total or Decimal('0')
            doc.total = (doc.neto_repuestos or Decimal('0')) + doc.neto_servicios + (doc.neto_otros_servicios or Decimal('0'))
            doc.save()
            print(f"✅ Total actualizado: ${doc.total} (anterior: ${total_anterior})")
            
        except Exception as e:
            print(f"❌ Error agregando servicio: {e}")
    else:
        for ls in servicios_existentes:
            print(f"   - {ls.nombre}: ${ls.precio_unitario}")

print("\n=== RESUMEN FINAL ===")
for doc in Documento.objects.filter(empresa=empresa).order_by('id'):
    rep_count = LineaServicio.objects.filter(documento=doc).count()  # Provisional
    serv_count = LineaServicio.objects.filter(documento=doc).count()  
    otros_count = LineaServicio.objects.filter(documento=doc).count()  # Provisional
    millas = doc.vehiculo.millas if doc.vehiculo else "No especificado"
    
    print(f"Doc {doc.pk} ({doc.tipo}): MILLAS={millas}, #SERV={serv_count}, TOTAL=${doc.total}")

print("\n✅ Agregado servicios a todos los documentos!")
