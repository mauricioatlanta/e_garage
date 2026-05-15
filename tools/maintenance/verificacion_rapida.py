#!/usr/bin/env python
import os
import sys

import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

print("🔍 VERIFICACIÓN RÁPIDA")
print("=" * 30)

try:
    from taller.models import Documento

    total = Documento.objects.count()
    print(f"📊 Total documentos: {total}")

    if total > 0:
        # Verificar primer documento
        primer_doc = Documento.objects.first()
        print(f"📄 Primer doc: #{primer_doc.numero_documento}")

        # Contar líneas del primer documento
        rep_c = primer_doc.lineas_repuesto.count()
        ser_c = primer_doc.lineas_servicio.count()
        otr_c = primer_doc.lineas_otro_servicio.count()

        print(f"   🔧 Líneas: rep={rep_c}, ser={ser_c}, otr={otr_c}")

        # Verificar últimos 5 documentos
        print("\n📄 ÚLTIMOS 5 DOCUMENTOS:")
        for doc in Documento.objects.order_by("-id")[:5]:
            rep_c = doc.lineas_repuesto.count()
            ser_c = doc.lineas_servicio.count()
            otr_c = doc.lineas_otro_servicio.count()
            total_lineas = rep_c + ser_c + otr_c
            print(f"   Doc {doc.id} #{doc.numero_documento}: {total_lineas} líneas total")

    else:
        print("❌ No hay documentos")

except Exception as e:
    print(f"❌ Error: {e}")

print("✅ OK")
