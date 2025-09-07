#!/usr/bin/env python
import os
import sys

import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from decimal import Decimal

from taller.documentos.models import Documento, LineaOtroServicio

print("Actualizando campo neto_otros_servicios para documentos...")

# Buscar documentos con otros servicios
docs_with_otros = Documento.objects.filter(
    lineas_otro_servicio__isnull=False
).distinct()

for doc in docs_with_otros:
    # Calcular el total de otros servicios
    otros_servicios = LineaOtroServicio.objects.filter(documento=doc)
    total_otros = sum(los.precio_cliente for los in otros_servicios)

    # Actualizar el campo
    doc.neto_otros_servicios = Decimal(str(total_otros))
    doc.save()

    print(
        f"Documento {doc.pk} ({doc.tipo}): neto_otros_servicios = ${doc.neto_otros_servicios}"
    )

print("¡Actualización completada!")
