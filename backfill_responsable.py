#!/usr/bin/env python
"""
Comando de backfill para flag "dividir por técnico/vendedor".
Cuando el flag está OFF, las líneas deben heredar el responsable del documento.
"""

import os
import sys

import django

# Configurar Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings.dev")
django.setup()

from django.db import transaction

from taller.models import Documento


def backfill_responsable():
    """Backfill del responsable en las líneas de documento."""
    print("🔄 Ejecutando backfill de responsable...")

    try:
        with transaction.atomic():
            documentos = Documento.objects.select_related("tecnico_responsable").all()
            total_docs = documentos.count()

            print(f"   Procesando {total_docs} documentos...")

            for i, d in enumerate(documentos, 1):
                if d.tecnico_responsable:
                    # Actualizar líneas de servicio
                    d.lineas_servicio.update(responsable=d.tecnico_responsable)

                    # Actualizar líneas de repuesto
                    d.lineas_repuesto.update(responsable=d.tecnico_responsable)

                    # Actualizar líneas de otro servicio
                    d.lineas_otro_servicio.update(responsable=d.tecnico_responsable)

                    if i % 100 == 0:
                        print(f"   Procesados {i}/{total_docs} documentos...")
                else:
                    print(f"   ⚠️  Documento {d.pk} sin técnico responsable")

            print(f"✅ Backfill completado para {total_docs} documentos")
            return True

    except Exception as e:
        print(f"❌ Error en backfill: {e}")
        return False


if __name__ == "__main__":
    backfill_responsable()
