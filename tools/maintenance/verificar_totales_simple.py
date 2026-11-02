#!/usr/bin/env python
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "egarage.settings")
django.setup()

from taller.models.documento import Documento
from taller.models.lineas_documento import (
    LineaOtroServicio,
    LineaRepuesto,
    LineaServicio,
)

print("=== DIAGNÓSTICO DE TOTALES ===")

# Verificar documentos
documentos = Documento.objects.all()[:5]
print(f"\nTotal documentos en BD: {Documento.objects.count()}")

for doc in documentos:
    print(f"\n--- Documento {doc.id} ---")
    print(f"Tipo: {doc.tipo}")
    print(f"Fecha: {doc.fecha}")

    # Verificar líneas de repuestos
    lineas_repuesto = doc.lineas_repuesto.all()
    print(f"Líneas repuesto: {lineas_repuesto.count()}")
    for linea in lineas_repuesto:
        print(
            f"  - {linea.nombre}: {linea.cantidad} x ${linea.precio_unitario} = ${linea.subtotal}"
        )

    # Verificar líneas de servicios
    lineas_servicio = doc.lineas_servicio.all()
    print(f"Líneas servicio: {lineas_servicio.count()}")
    for linea in lineas_servicio:
        print(
            f"  - {linea.nombre}: {linea.cantidad} x ${linea.precio_unitario} = ${linea.subtotal}"
        )

    # Verificar otros servicios
    lineas_otros = doc.lineas_otro_servicio.all()
    print(f"Líneas otros servicios: {lineas_otros.count()}")
    for linea in lineas_otros:
        print(
            f"  - {linea.nombre}: {linea.cantidad} x ${linea.precio_unitario} = ${linea.subtotal}"
        )

    # Calcular totales
    total_repuestos = doc.total_repuestos()
    total_servicios = doc.total_servicios()
    total_general = doc.total_general()

    print(f"TOTAL REPUESTOS: ${total_repuestos}")
    print(f"TOTAL SERVICIOS: ${total_servicios}")
    print(f"TOTAL GENERAL: ${total_general}")

# Verificar totales globales
print("\n=== TOTALES GLOBALES ===")
print(f"Total líneas repuesto: {LineaRepuesto.objects.count()}")
print(f"Total líneas servicio: {LineaServicio.objects.count()}")
print(f"Total líneas otros servicios: {LineaOtroServicio.objects.count()}")

print("\n=== DIAGNÓSTICO COMPLETADO ===")
