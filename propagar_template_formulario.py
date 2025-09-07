#!/usr/bin/env python3
"""
Script para propagar cambios del template de crear vehículo
a todas las variantes de idioma
"""

import os
import shutil


def propagar_template():
    print("🔄 Propagando template de crear vehículo...")

    # Template fuente
    template_source = "templates_canonical/taller/vehiculos/crear_vehiculo.html"

    # Templates destino (múltiples idiomas)
    templates_destino = [
        "templates/CL/ES/taller/vehiculos/crear_vehiculo.html",
        "templates/CL/EN/taller/vehiculos/crear_vehiculo.html",
        "templates/US/ES/taller/vehiculos/crear_vehiculo.html",
        "templates/US/EN/taller/vehiculos/crear_vehiculo.html",
    ]

    # Verificar que el archivo fuente existe
    if not os.path.exists(template_source):
        print(f"❌ Error: No se encontró el archivo fuente {template_source}")
        return

    print(f"📂 Archivo fuente: {template_source}")

    # Copiar archivo a todos los idiomas
    for destino in templates_destino:
        try:
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(destino), exist_ok=True)

            # Copiar archivo
            shutil.copy2(template_source, destino)
            print(f"✅ Copiado a {destino}")
        except Exception as e:
            print(f"❌ Error copiando a {destino}: {e}")

    print("\n✅ Template propagado a todas las variantes")
    print("📋 Cambios aplicados:")
    print("  • Agregado action='{% url 'taller:vehiculos:crear' %}' al formulario")
    print("  • Agregado id='form-crear-vehiculo' al formulario")
    print("  • Agregado logger de JavaScript para debug")
    print("  • Configurado namespace correcto en URLs")


if __name__ == "__main__":
    propagar_template()
