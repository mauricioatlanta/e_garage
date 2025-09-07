#!/usr/bin/env python3
"""
Script para actualizar todos los templates de editar_vehiculo con la nueva versión
"""

import os
import shutil


def actualizar_templates_editar_vehiculo():
    """Actualiza todos los templates de editar_vehiculo con la versión mejorada"""

    print("🔄 ACTUALIZANDO TEMPLATES DE EDITAR VEHÍCULO")
    print("=" * 60)

    # Template fuente
    template_fuente = "templates_canonical/taller/vehiculos/editar_vehiculo.html"

    # Templates a actualizar
    templates_destino = [
        "templates_canonical/taller/cl/es/vehiculos/editar_vehiculo.html",
        "templates_canonical/taller/cl/en/vehiculos/editar_vehiculo.html",
        "templates_canonical/taller/us/es/vehiculos/editar_vehiculo.html",
        "templates_canonical/taller/us/en/vehiculos/editar_vehiculo.html",
        "templates/taller/vehiculos/editar_vehiculo.html",
        "taller/vehiculos/templates/taller/vehiculos/editar_vehiculo.html",
    ]

    if not os.path.exists(template_fuente):
        print(f"❌ Template fuente no encontrado: {template_fuente}")
        return False

    print(f"📂 Template fuente: {template_fuente}")
    print(f"✅ Template fuente encontrado")

    actualizados = 0

    for destino in templates_destino:
        try:
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(destino), exist_ok=True)

            # Copiar template
            shutil.copy2(template_fuente, destino)
            print(f"✅ Actualizado: {destino}")
            actualizados += 1

        except Exception as e:
            print(f"❌ Error actualizando {destino}: {e}")

    print("=" * 60)
    print(f"🎉 ACTUALIZACIÓN COMPLETADA")
    print(f"📊 Templates actualizados: {actualizados}/{len(templates_destino)}")

    return True


if __name__ == "__main__":
    try:
        if actualizar_templates_editar_vehiculo():
            print("\n✅ TODOS LOS TEMPLATES DE EDITAR VEHÍCULO ACTUALIZADOS")
        else:
            print("\n❌ HUBO ERRORES EN LA ACTUALIZACIÓN")
    except Exception as e:
        print(f"\n💥 ERROR CRÍTICO: {e}")
