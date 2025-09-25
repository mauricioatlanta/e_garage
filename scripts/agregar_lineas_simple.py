#!/usr/bin/env python
"""
Script simple para agregar líneas de ejemplo a documentos
"""

import os
import sys
from decimal import Decimal

import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from taller.models.documento import Documento
from taller.models.lineas_documento import LineaRepuesto, LineaServicio


def agregar_lineas_simple():
    print("💰 Agregando líneas de ejemplo a documentos...")

    # Obtener todos los documentos
    documentos = Documento.objects.all()

    if not documentos:
        print("❌ No hay documentos en el sistema.")
        return

    print(f"📄 Encontrados {documentos.count()} documentos")

    for doc in documentos:
        print(f"\n📋 Procesando documento ID: {doc.id}")

        # Agregar línea de servicio simple
        try:
            LineaServicio.objects.get_or_create(
                documento=doc,
                nombre="Cambio de aceite",
                defaults={
                    "cantidad": 1,
                    "precio_unitario": (
                        Decimal("50000")
                        if doc.empresa.pais == "CL"
                        else Decimal("89.99")
                    ),
                    "descuento": Decimal("0.00"),
                    "observaciones": "Servicio de cambio de aceite completo",
                },
            )
            print("   ✅ Servicio agregado")
        except Exception as e:
            print(f"   ❌ Error agregando servicio: {e}")

        # Agregar línea de repuesto simple
        try:
            LineaRepuesto.objects.get_or_create(
                documento=doc,
                codigo="REP-001",
                nombre="Filtro de aceite",
                defaults={
                    "cantidad": 1,
                    "precio_unitario": (
                        Decimal("8500")
                        if doc.empresa.pais == "CL"
                        else Decimal("24.99")
                    ),
                    "descuento": Decimal("0.00"),
                    "observaciones": "Filtro de aceite original",
                },
            )
            print("   ✅ Repuesto agregado")
        except Exception as e:
            print(f"   ❌ Error agregando repuesto: {e}")

    print("\n✅ ¡Proceso completado!")
    print("🌐 Ahora puedes ver el listado de documentos con totales")


if __name__ == "__main__":
    agregar_lineas_simple()
