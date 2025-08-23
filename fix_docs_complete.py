#!/usr/bin/env python
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from taller.documentos.models import Documento, LineaOtroServicio
from taller.servicios.models import ServicioExterno
from taller.models import Empresa
from taller.models.vehiculos import Vehiculo
from decimal import Decimal

print("=== DIAGNÓSTICO DE DOCUMENTOS ===")

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

for doc in docs:
    print(f"\n--- Documento {doc.pk} ({doc.tipo}) ---")
    
    # Verificar vehículo y millas
    if doc.vehiculo:
        print(f"🚗 Vehículo: {doc.vehiculo}")
        print(f"📏 Millas actuales: {doc.vehiculo.millas}")
        
        # Actualizar millas si están vacías
        if not doc.vehiculo.millas:
            doc.vehiculo.millas = 85000
            doc.vehiculo.save()
            print(f"✅ Millas actualizadas a: {doc.vehiculo.millas}")
    else:
        print("❌ Sin vehículo asociado")
    
    # Verificar otros servicios
    otros_servicios = LineaOtroServicio.objects.filter(documento=doc)
    print(f"🔧 Otros servicios: {otros_servicios.count()}")
    
    for los in otros_servicios:
        print(f"   - {los.nombre}: ${los.precio_cliente}")
    
    # Si no tiene otros servicios, agregar uno
    if otros_servicios.count() == 0:
        try:
            servicio_ext = ServicioExterno.objects.filter(empresa=empresa).first()
            if servicio_ext:
                los = LineaOtroServicio.objects.create(
                    documento=doc,
                    servicio_externo=servicio_ext,
                    nombre=servicio_ext.nombre,
                    empresa_externa=servicio_ext.empresa_externa,
                    cantidad=Decimal('1'),
                    costo_interno=servicio_ext.costo_taller,
                    precio_cliente=servicio_ext.precio_cliente
                )
                print(f"✅ Servicio agregado: {los.nombre} - ${los.precio_cliente}")
                
                # Actualizar totales del documento
                doc.neto_otros_servicios = los.precio_cliente
                doc.total = (doc.neto_repuestos or Decimal('0')) + (doc.neto_servicios or Decimal('0')) + doc.neto_otros_servicios
                doc.save()
                print(f"✅ Total actualizado: ${doc.total}")
            else:
                print("❌ No hay servicios externos disponibles")
        except Exception as e:
            print(f"❌ Error agregando servicio: {e}")

print("\n=== RESUMEN FINAL ===")
for doc in Documento.objects.filter(empresa=empresa).order_by('id'):
    rep_count = doc.lineas_repuesto.count()
    serv_count = doc.lineas_servicio.count()  
    otros_count = LineaOtroServicio.objects.filter(documento=doc).count()
    millas = doc.vehiculo.millas if doc.vehiculo else "No especificado"
    
    print(f"Doc {doc.pk} ({doc.tipo}): MILLAS={millas}, #REP={rep_count}, #SERV={serv_count}, #OTROS={otros_count}, TOTAL=${doc.total}")

print("\n✅ Diagnóstico y corrección completados!")
