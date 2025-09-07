#!/usr/bin/env python
"""
Script para corregir las URLs de eliminación de clientes en todos los templates
"""

import os
import re
from pathlib import Path


def fix_delete_urls_in_file(file_path):
    """Corrige las URLs de eliminación en un archivo"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Patrón para encontrar la URL incorrecta
        old_pattern = r"{% url 'taller:clientes:delete' pk=cliente\.pk %}"
        new_pattern = (
            "{% url 'taller:clientes:eliminar_cliente' cliente_id=cliente.pk %}"
        )

        # Reemplazar si existe el patrón
        if re.search(old_pattern, content):
            content = re.sub(old_pattern, new_pattern, content)

            # Escribir el archivo corregido
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            print(f"✅ Corregido: {file_path}")
            return True
        else:
            print(f"⏭️  Sin cambios: {file_path}")
            return False

    except Exception as e:
        print(f"❌ Error en {file_path}: {e}")
        return False


def main():
    """Función principal"""
    print("🔧 CORRIGIENDO URLs DE ELIMINACIÓN DE CLIENTES")
    print("=" * 60)

    # Lista de archivos que necesitan corrección
    files_to_fix = [
        "templates_canonical/taller/cl/es/clientes/_tabla_clientes.html",
        "templates/us/es/clientes/lista_clientes.html",
        "templates/us/es/clientes/cliente_list.html",
        "templates/us/en/clientes/lista_clientes.html",
        "templates/us/en/clientes/cliente_list.html",
        "templates/taller/clientes/_tabla_clientes.html",
        "templates/taller/clientes/confirmar_eliminacion.html",
        "templates/taller/cliente_list.html",
        "templates/taller/cliente_detail.html",
        "templates/cl/es/clientes/_tabla_clientes.html",
        "templates/cl/es/clientes/lista_clientes.html",
        "templates/cl/es/clientes/cliente_list.html",
        "templates_new/templates/taller/cl/es/common/cliente_list.html",
        "templates_new/templates/taller/cl/es/common/cliente_detail.html",
        "templates_new/templates/taller/cl/es/clientes/_tabla_clientes.html",
        "templates_new/templates/taller/cl/es/clientes/lista_clientes.html",
        "templates_canonical/taller/us/es/clientes/lista_clientes.html",
        "templates_canonical/taller/us/es/clientes/cliente_list.html",
        "templates_canonical/taller/us/en/clientes/lista_clientes.html",
        "templates_canonical/taller/cl/en/clientes/lista_clientes.html",
        "templates_canonical/taller/cl/en/clientes/cliente_list.html",
    ]

    corrected_count = 0
    total_files = len(files_to_fix)

    for file_path in files_to_fix:
        if os.path.exists(file_path):
            if fix_delete_urls_in_file(file_path):
                corrected_count += 1
        else:
            print(f"⚠️  Archivo no encontrado: {file_path}")

    print("\n" + "=" * 60)
    print(f"📊 RESUMEN:")
    print(f"   • Archivos procesados: {total_files}")
    print(f"   • Archivos corregidos: {corrected_count}")
    print(f"   • Archivos sin cambios: {total_files - corrected_count}")
    print("\n✅ CORRECCIÓN COMPLETADA!")
    print(
        "   Las URLs de eliminación ahora usan 'eliminar_cliente' en lugar de 'delete'"
    )


if __name__ == "__main__":
    main()
