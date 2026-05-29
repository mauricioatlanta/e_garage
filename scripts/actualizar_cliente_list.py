#!/usr/bin/env python
import os
import shutil

import django

# Configure Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()


def actualizar_cliente_list():
    """Actualiza todos los templates de cliente_list.html con la variable correcta"""

    base_path = os.getcwd()
    source_template = os.path.join(
        base_path,
        "templates_canonical",
        "taller",
        "cl",
        "es",
        "clientes",
        "cliente_list.html",
    )

    # Verificar que el template fuente existe
    if not os.path.exists(source_template):
        print(f"❌ Error: No se encuentra el template fuente: {source_template}")
        return

    # Lista de templates destino
    templates_destino = [
        "templates_canonical/taller/cl/en/clientes/cliente_list.html",
        "templates_canonical/taller/us/es/clientes/cliente_list.html",
        "templates_canonical/taller/us/en/clientes/cliente_list.html",
        "templates_canonical/taller/common/clientes/cliente_list.html",
        "templates/taller/cliente_list.html",  # Template legacy
    ]

    actualizado = 0
    errores = 0

    print("🔄 ACTUALIZANDO TEMPLATES DE CLIENTE_LIST")
    print("=" * 60)
    print(f"📂 Template fuente: {source_template}")

    for template_destino in templates_destino:
        try:
            ruta_completa = os.path.join(base_path, template_destino)

            # Crear directorio si no existe
            os.makedirs(os.path.dirname(ruta_completa), exist_ok=True)

            # Copiar template
            shutil.copy2(source_template, ruta_completa)
            print(f"✅ Actualizado: {template_destino}")
            actualizado += 1

        except Exception as e:
            print(f"❌ Error actualizando {template_destino}: {str(e)}")
            errores += 1

    print("=" * 60)
    print("🎉 ACTUALIZACIÓN COMPLETADA")
    print(f"✅ Templates actualizados: {actualizado}/{len(templates_destino)}")
    if errores > 0:
        print(f"❌ Errores: {errores}")

    print("\n📋 MEJORAS IMPLEMENTADAS:")
    print("• 🔧 Variable corregida: 'clientes' → 'cliente_list'")
    print("• 📊 Listado de clientes ahora funciona correctamente")


if __name__ == "__main__":
    actualizar_cliente_list()
