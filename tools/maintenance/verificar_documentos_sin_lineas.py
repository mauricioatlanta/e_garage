#!/usr/bin/env python
import os
import sys

import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.db.models import Count

from taller.models import Documento

print("🔍 VERIFICACIÓN DE DOCUMENTOS SIN LÍNEAS")
print("=" * 50)

# Conteo total
total = Documento.objects.count()

# Documentos con alguna línea
con_lineas = (
    (
        Documento.objects.annotate(
            rep=Count("lineas_repuesto"),
            ser=Count("lineas_servicio"),
            otr=Count("lineas_otro_servicio"),
        ).filter(rep__gt=0)
        | Documento.objects.annotate(
            rep=Count("lineas_repuesto"),
            ser=Count("lineas_servicio"),
            otr=Count("lineas_otro_servicio"),
        ).filter(ser__gt=0)
        | Documento.objects.annotate(
            rep=Count("lineas_repuesto"),
            ser=Count("lineas_servicio"),
            otr=Count("lineas_otro_servicio"),
        ).filter(otr__gt=0)
    )
    .distinct()
    .count()
)

print(f"📊 TOTAL docs: {total}, con alguna línea: {con_lineas}")
print(f"📊 Sin líneas: {total - con_lineas}")
print()

print("📄 ÚLTIMOS 15 DOCUMENTOS:")
print("-" * 50)
for d in Documento.objects.order_by("-id")[:15]:
    rep_count = d.lineas_repuesto.count()
    ser_count = d.lineas_servicio.count()
    otr_count = d.lineas_otro_servicio.count()

    print(f"📄 Doc {d.id} #{getattr(d, 'numero_documento', 'N/A')}")
    print(f"   🔧 rep/ser/otr= {rep_count}/{ser_count}/{otr_count}")
    print(
        f"   💰 netos= rep:{getattr(d, 'neto_repuestos', 'N/A')} ser:{getattr(d, 'neto_servicios', 'N/A')}"
    )
    print()

print("✅ Verificación completada")
