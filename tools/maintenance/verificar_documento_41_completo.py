#!/usr/bin/env python
import os

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from taller.models.documento import Documento

try:
    doc = Documento.objects.get(id=41)
    print(f"📄 Documento: {doc.numero_documento}")
    print(f"📅 Fecha: {doc.fecha}")
    print(f"📅 Tipo de fecha: {type(doc.fecha)}")
    print(f"👤 Cliente: {doc.cliente}")
    print(f"🚗 Vehículo: {doc.vehiculo}")
    print(f"🔧 Mecánico: {doc.mecanico}")
    print(f'🔧 Mecánico ID: {doc.mecanico.id if doc.mecanico else "None"}')
    print(f'🔧 Mecánico Nombre: {doc.mecanico.nombre if doc.mecanico else "None"}')

    # Listar mecánicos disponibles para la empresa
    mecanicos = Tecnico.objects.filter(empresa=doc.empresa)
    print(f"\n🔧 Mecánicos disponibles para {doc.empresa}:")
    for m in mecanicos:
        print(f"   - {m.nombre} (ID: {m.id})")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()
