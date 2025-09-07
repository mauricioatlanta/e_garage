#!/usr/bin/env python3
"""
Script para actualizar todos los templates de crear_cliente con la nueva versión futurística
"""

import os
import shutil


def actualizar_templates_crear_cliente():
    """Actualiza todos los templates de crear_cliente con la versión mejorada"""

    print("🔄 ACTUALIZANDO TEMPLATES DE CREAR CLIENTE")
    print("=" * 60)

    # Template fuente (Chile ES que acabamos de actualizar)
    template_fuente = "templates_canonical/taller/cl/es/clientes/crear_cliente.html"

    # Templates a actualizar
    templates_destino = [
        "templates_canonical/taller/cl/en/clientes/crear_cliente.html",
        "templates_canonical/taller/us/es/clientes/crear_cliente.html",
        "templates_canonical/taller/us/en/clientes/crear_cliente.html",
        "templates/taller/clientes/crear_cliente.html",
        "taller/clientes/templates/taller/clientes/crear_cliente.html",
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
    print(f"✅ Templates actualizados: {actualizados}/{len(templates_destino)}")

    print("\n📋 MEJORAS IMPLEMENTADAS:")
    print("• 🎨 Gráficos futuristas y tecnológicos")
    print("• 🌈 Mejor contraste en campos de formulario")
    print("• 📍 Campo dirección reordenado (antes de región/ciudad)")
    print("• 🔧 JavaScript mejorado para carga de ciudades")
    print("• ✨ Animaciones y efectos avanzados")
    print("• 🎯 Mejor debugging y manejo de errores")

    return True


if __name__ == "__main__":
    actualizar_templates_crear_cliente()
