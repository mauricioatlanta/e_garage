#!/usr/bin/env python
"""
Prueba de humo para verificar documentos y líneas
"""

import os
import sys

import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

print("🔍 PRUEBA DE HUMO - DOCUMENTOS")
print("=" * 40)

try:
    from taller.models import Documento

    d = Documento.objects.order_by("-id").first()
    if d:
        rep_count = d.lineas_repuesto.count()
        serv_count = d.lineas_servicio.count()
        otr_count = d.lineas_otro_servicio.count()

        print(
            f"✅ DOC {d.id} {d.empresa.country} rep/serv/otr= {rep_count}/{serv_count}/{otr_count}"
        )

        if rep_count > 0 or serv_count > 0 or otr_count > 0:
            print("✅ El último documento SÍ tiene líneas")
        else:
            print("⚠️ El último documento NO tiene líneas")

        # Verificar total de documentos
        total_docs = Documento.objects.count()
        docs_con_lineas = (
            Documento.objects.filter(lineas_repuesto__isnull=False).distinct().count()
        )

        print(f"📊 Total docs: {total_docs}, con líneas rep: {docs_con_lineas}")

    else:
        print("❌ No hay documentos en la base de datos")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()

print("✅ Prueba de humo completada")
