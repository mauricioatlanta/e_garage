#!/usr/bin/env python
import os

import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from taller.models.documento import Documento
from taller.models.lineas_documento import LineaOtroServicio, LineaServicio

# Buscar el último documento creado
doc = Documento.objects.last()
if not doc:
    print("No hay documentos en la base de datos")
    exit()

print(f"=== ANÁLISIS DOCUMENTO ID: {doc.id} ===")
print(f"Número: {doc.numero_documento}")
print(f"Cliente: {doc.cliente.nombre} {doc.cliente.apellido}")
print(f"Vehículo: {doc.vehiculo.patente} - {doc.vehiculo.marca} {doc.vehiculo.modelo}")
print(f"Kilometraje del vehículo: {getattr(doc.vehiculo, 'millas', 'No especificado')} millas/km")

# Verificar servicios directamente desde las tablas
servicios = LineaServicio.objects.filter(documento=doc)
print(f"\n=== SERVICIOS INTERNOS ({servicios.count()}) ===")
for s in servicios:
    print(f"  ID: {s.id} - {s.nombre}: ${s.precio_unitario} x {s.cantidad}")

# Verificar otros servicios
otros = LineaOtroServicio.objects.filter(documento=doc)
print(f"\n=== OTROS SERVICIOS ({otros.count()}) ===")
for o in otros:
    precio = getattr(o, 'precio_cliente', 0)
    empresa = getattr(o, 'empresa_externa', 'No especificada')
    print(f"  ID: {o.id} - {o.nombre}: ${precio} ({empresa})")

# Verificar repuestos usando related manager
try:
    repuestos = doc.lineas_repuesto.all()
    print(f"\n=== REPUESTOS ({repuestos.count()}) ===")
    for r in repuestos:
        print(f"  ID: {r.id} - {r.repuesto.nombre}: ${r.precio_unitario} x {r.cantidad}")
except Exception as e:
    print(f"\n=== REPUESTOS (Error: {e}) ===")

# Verificar totales guardados
print(f"\n=== TOTALES GUARDADOS ===")
print(f"Neto repuestos: ${doc.neto_repuestos}")
print(f"Neto servicios: ${doc.neto_servicios}")
print(f"Total: ${doc.total}")

print(f"\n=== VERIFICACIÓN COMPLETA ===")
print("✅ Análisis completado")
