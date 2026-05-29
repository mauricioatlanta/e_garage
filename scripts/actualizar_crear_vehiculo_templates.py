#!/usr/bin/env python3
"""
Script para actualizar el template de crear vehículo en todas las variantes de país/idioma
"""

import shutil
from pathlib import Path


def main():
    # Ruta base del proyecto
    base_path = Path(__file__).parent
    templates_path = base_path / "templates_canonical"

    # Template fuente (el que acabamos de crear)
    source_template = templates_path / "taller" / "vehiculos" / "crear_vehiculo.html"

    # Lista de variantes de templates a actualizar
    variants = [
        "taller/common/vehiculos/crear_vehiculo.html",
        "taller/cl/es/vehiculos/crear_vehiculo.html",
        "taller/cl/en/vehiculos/crear_vehiculo.html",
        "taller/us/es/vehiculos/crear_vehiculo.html",
        "taller/us/en/vehiculos/crear_vehiculo.html",
    ]

    print("🛠️ Actualizando templates de crear vehículo...")
    print(f"📂 Fuente: {source_template}")

    updated_count = 0

    for variant in variants:
        target_path = templates_path / variant

        try:
            # Crear directorios si no existen
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # Copiar el template actualizado
            shutil.copy2(source_template, target_path)
            print(f"✅ Actualizado: {variant}")
            updated_count += 1

        except Exception as e:
            print(f"❌ Error actualizando {variant}: {e}")

    print("\n🎉 ACTUALIZACIÓN COMPLETADA")
    print(f"✅ Templates actualizados: {updated_count}/{len(variants)}")
    print("🚀 El nuevo template de crear vehículo está listo!")


if __name__ == "__main__":
    main()
