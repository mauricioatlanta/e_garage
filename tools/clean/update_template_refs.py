#!/usr/bin/env python
"""
Actualiza referencias a archivos estáticos en templates y archivos CSS/JS
"""

import argparse
import json
import re
import shutil
from pathlib import Path


def backup_file(file_path):
    """Crea backup de un archivo"""
    backup_path = file_path.with_suffix(file_path.suffix + ".bak")
    shutil.copy2(file_path, backup_path)
    return backup_path


def update_file_references(file_path, manifest, dry_run=True):
    """Actualiza referencias en un archivo"""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        original_content = content
        changes_made = 0

        # Patrones de búsqueda para diferentes tipos de referencias
        patterns = [
            # Django static tags
            r'{%\s*static\s+[\'"]([^\'"]+)[\'"]\s*%}',
            # CSS url()
            r'url\([\'"]?([^\'")]+)[\'"]?\)',
            # HTML src/href
            r'(?:src|href)=[\'"]([^\'"]+)[\'"]',
            # JavaScript imports/requires
            r'(?:import|require)\([\'"]([^\'"]+)[\'"]\)',
            # CSS @import
            r'@import\s+[\'"]([^\'"]+)[\'"]',
        ]

        for pattern in patterns:

            def replace_ref(match):
                nonlocal changes_made
                ref_path = match.group(1)

                # Buscar en manifest
                if ref_path in manifest:
                    new_path = manifest[ref_path]
                    changes_made += 1
                    return match.group(0).replace(ref_path, new_path)

                return match.group(0)

            content = re.sub(pattern, replace_ref, content)

        if changes_made > 0:
            if not dry_run:
                # Crear backup
                backup_path = backup_file(file_path)

                # Escribir archivo actualizado
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)

                print(
                    f"   ✅ {file_path} - {changes_made} referencias actualizadas (backup: {backup_path.name})"
                )
            else:
                print(f"   📝 {file_path} - {changes_made} referencias a actualizar")

            return changes_made
        else:
            return 0

    except Exception as e:
        print(f"   ❌ Error procesando {file_path}: {e}")
        return 0


def update_template_references(templates_dir, static_dir, manifest_file, dry_run=True):
    """Actualiza referencias en templates y archivos estáticos"""
    templates_path = Path(templates_dir)
    static_path = Path(static_dir)

    if not templates_path.exists():
        print(f"❌ Directorio de templates no existe: {templates_path}")
        return

    if not static_path.exists():
        print(f"❌ Directorio de static no existe: {static_path}")
        return

    # Cargar manifest
    with open(manifest_file, encoding="utf-8") as f:
        manifest = json.load(f)

    print("🔍 Actualizando referencias...")
    print(f"   Templates: {templates_path}")
    print(f"   Static: {static_path}")
    print(f"   Manifest: {manifest_file}")
    print(f"   Modo: {'DRY RUN' if dry_run else 'APLICAR CAMBIOS'}")

    total_files = 0
    total_changes = 0

    # Procesar templates HTML
    print("\n📄 Procesando templates HTML...")
    for html_file in templates_path.rglob("*.html"):
        changes = update_file_references(html_file, manifest, dry_run)
        if changes > 0:
            total_files += 1
            total_changes += changes

    # Procesar archivos CSS
    print("\n🎨 Procesando archivos CSS...")
    for css_file in static_path.rglob("*.css"):
        changes = update_file_references(css_file, manifest, dry_run)
        if changes > 0:
            total_files += 1
            total_changes += changes

    # Procesar archivos JavaScript
    print("\n⚡ Procesando archivos JavaScript...")
    for js_file in static_path.rglob("*.js"):
        changes = update_file_references(js_file, manifest, dry_run)
        if changes > 0:
            total_files += 1
            total_changes += changes

    # Resumen
    print("\n📊 RESUMEN:")
    print(f"   Archivos procesados: {total_files}")
    print(f"   Referencias actualizadas: {total_changes}")

    if dry_run:
        print("\n💡 Para aplicar los cambios, ejecuta:")
        print(
            f"   python update_template_refs.py --templates {templates_path} --static {static_path} --manifest {manifest_file}"
        )
    else:
        print("\n✅ Cambios aplicados exitosamente")
        print("   Los archivos originales se guardaron con extensión .bak")


def main():
    parser = argparse.ArgumentParser(
        description="Actualiza referencias a archivos estáticos"
    )
    parser.add_argument("--templates", required=True, help="Directorio de templates")
    parser.add_argument(
        "--static", required=True, help="Directorio de archivos estáticos"
    )
    parser.add_argument("--manifest", required=True, help="Archivo JSON de manifest")
    parser.add_argument(
        "--dry", action="store_true", help="Solo mostrar cambios sin aplicarlos"
    )

    args = parser.parse_args()
    update_template_references(args.templates, args.static, args.manifest, args.dry)


if __name__ == "__main__":
    main()
