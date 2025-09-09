#!/usr/bin/env python
import os

import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from taller.models.documento import Documento
from taller.models.lineas_documento import LineaOtroServicio, LineaServicio


def verificar_documento_44():
    """Verificar específicamente el documento 44"""
    try:
        doc = Documento.objects.get(id=44)
        print(f"=== DOCUMENTO ID: {doc.id} ===")
        print(f"Número: {doc.numero_documento}")
        print(f"Cliente: {doc.cliente.nombre} {doc.cliente.apellido}")
        print(f"Vehículo: {doc.vehiculo.patente} - {doc.vehiculo.marca} {doc.vehiculo.modelo}")
        print(f"Kilometraje del vehículo: {getattr(doc.vehiculo, 'millas', 'No especificado')} millas/km")
        
        # Verificar servicios usando related manager
        try:
            servicios_rm = doc.lineas_servicio.all()
            print(f"\n=== SERVICIOS VIA RELATED MANAGER ({servicios_rm.count()}) ===")
            for s in servicios_rm:
                print(f"  - {s.nombre}: ${s.precio_unitario} x {s.cantidad}")
        except Exception as e:
            print(f"Error con related manager servicios: {e}")
            
        # Verificar servicios con filtro directo
        servicios_filter = LineaServicio.objects.filter(documento=doc)
        print(f"\n=== SERVICIOS VIA FILTER ({servicios_filter.count()}) ===")
        for s in servicios_filter:
            print(f"  - {s.nombre}: ${s.precio_unitario} x {s.cantidad}")
        
        # Verificar otros servicios usando related manager
        try:
            otros_rm = doc.lineas_otro_servicio.all()
            print(f"\n=== OTROS SERVICIOS VIA RELATED MANAGER ({otros_rm.count()}) ===")
            for o in otros_rm:
                precio = getattr(o, 'precio_cliente', 0)
                empresa = getattr(o, 'empresa_externa', 'No especificada')
                print(f"  - {o.nombre}: ${precio} ({empresa})")
        except Exception as e:
            print(f"Error con related manager otros servicios: {e}")
            
        # Verificar otros servicios con filtro directo
        otros_filter = LineaOtroServicio.objects.filter(documento=doc)
        print(f"\n=== OTROS SERVICIOS VIA FILTER ({otros_filter.count()}) ===")
        for o in otros_filter:
            precio = getattr(o, 'precio_cliente', 0)
            empresa = getattr(o, 'empresa_externa', 'No especificada')
            print(f"  - {o.nombre}: ${precio} ({empresa})")
        
        # Verificar repuestos
        try:
            repuestos = doc.lineas_repuesto.all()
            print(f"\n=== REPUESTOS ({repuestos.count()}) ===")
            for r in repuestos:
                print(f"  - {r.repuesto.nombre}: ${r.precio_unitario} x {r.cantidad}")
        except Exception as e:
            print(f"Error con repuestos: {e}")
            
        # Verificar totales
        print(f"\n=== TOTALES ===")
        print(f"Neto repuestos: ${doc.neto_repuestos}")
        print(f"Neto servicios: ${doc.neto_servicios}")
        print(f"Total: ${doc.total}")
        
        return doc
        
    except Documento.DoesNotExist:
        print("❌ Documento 44 no encontrado")
        return None
    except Exception as e:
        print(f"❌ Error verificando documento 44: {e}")
        return None

if __name__ == "__main__":
    doc = verificar_documento_44()
    if doc:
        print("\n✅ Verificación completada")
    else:
        print("\n❌ Verificación falló")
