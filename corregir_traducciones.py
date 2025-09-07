#!/usr/bin/env python
"""
Script mejorado para completar traducciones específicas
"""
import os
import sys

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from taller.servicios.models import Servicio, ServicioName


def corregir_traducciones():
    """Corregir y completar traducciones específicas"""
    print("🔍 Corrigiendo traducciones específicas...")

    # Buscar el servicio que necesita corrección
    servicio = Servicio.objects.filter(code="cambio_aceite_motor").first()

    if servicio:
        print(f"📋 Encontrado servicio: {servicio.code}")

        # Verificar si ya existe traducción al inglés
        traduccion_en = servicio.names.filter(language="en").first()

        if traduccion_en:
            # Actualizar traducción existente
            traduccion_en.label = "Engine Oil Change"
            traduccion_en.aliases = ["oil change", "motor oil", "lubricant change"]
            traduccion_en.save()
            print(f"   ✅ Traducción actualizada: 'Engine Oil Change'")
        else:
            # Crear nueva traducción
            ServicioName.objects.create(
                servicio=servicio,
                language="en",
                label="Engine Oil Change",
                aliases=["oil change", "motor oil", "lubricant change"],
                is_default=True,
            )
            print(f"   ✅ Traducción creada: 'Engine Oil Change'")

    print(f"\n🎉 Corrección completada exitosamente")


if __name__ == "__main__":
    corregir_traducciones()
