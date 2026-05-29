#!/usr/bin/env python
"""
KPI sanity check usando solo fecha_emision.
Verifica que los cálculos de KPIs funcionen correctamente.
"""

import os
import sys

import django

# Configurar Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings.dev")
django.setup()

from django.db.models import DecimalField, ExpressionWrapper, F, Sum
from django.utils import timezone

from taller.models import Documento, LineaServicio, Tecnico


def kpi_sanity_check():
    """Verifica que los KPIs funcionen correctamente."""
    print("📊 Ejecutando KPI sanity check...")

    try:
        # KPI 1: Totales por técnico en el mes actual
        print("\n1. Totales por técnico en el mes actual:")
        monto = ExpressionWrapper(
            F("cantidad") * F("precio_unitario") * (1 - F("descuento")),
            output_field=DecimalField(max_digits=14, decimal_places=2),
        )

        totales = (
            LineaServicio.objects.filter(documento__fecha_emision__month=timezone.now().month)
            .annotate(monto=monto)
            .values("documento__tecnico_responsable__nombre")
            .annotate(total=Sum("monto"))
        )

        print("   Resultados:")
        for total in totales:
            print(f"   - {total['documento__tecnico_responsable__nombre']}: ${total['total']}")

        # KPI 2: Documentos por estado en el mes actual
        print("\n2. Documentos por estado en el mes actual:")
        docs_por_estado = (
            Documento.objects.filter(fecha_emision__month=timezone.now().month)
            .values("estado")
            .annotate(total=Sum("id"))
        )

        print("   Resultados:")
        for estado in docs_por_estado:
            print(f"   - {estado['estado']}: {estado['total']} documentos")

        # KPI 3: Técnicos más activos
        print("\n3. Técnicos más activos:")
        tecnicos_activos = (
            Tecnico.objects.filter(documento__fecha_emision__month=timezone.now().month)
            .values("nombre")
            .annotate(total_docs=Sum("documento__id"))
        )

        print("   Resultados:")
        for tecnico in tecnicos_activos:
            print(f"   - {tecnico['nombre']}: {tecnico['total_docs']} documentos")

        print("\n✅ KPI sanity check completado")
        return True

    except Exception as e:
        print(f"❌ Error en KPI sanity check: {e}")
        return False


if __name__ == "__main__":
    kpi_sanity_check()
