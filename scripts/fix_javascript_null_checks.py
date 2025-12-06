#!/usr/bin/env python3
"""
Script para corregir getElementById().addEventListener sin verificación
Agrega verificación if (element) antes de addEventListener
"""

import os
import re
from pathlib import Path

# Patrón para encontrar getElementById().addEventListener sin verificación
PATTERN = re.compile(
    r"(\s*)document\.getElementById\(([^)]+)\)\.addEventListener\s*\(", re.MULTILINE
)

# Patrón alternativo: getElementById en una línea, addEventListener en otra
PATTERN_MULTILINE = re.compile(
    r"(\s*)const\s+(\w+)\s*=\s*document\.getElementById\(([^)]+)\)\s*;\s*\n\s*\2\.addEventListener\s*\(",
    re.MULTILINE,
)


def fix_javascript_file(file_path):
    """Corrige un archivo JavaScript/HTML con problemas de null check"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content
        changes_made = []

        # Fix patrón 1: document.getElementById('id').addEventListener
        def replace_pattern1(match):
            indent = match.group(1)
            element_id = match.group(2)
            var_name = f"el_{element_id.strip('\"\'')}"

            replacement = f"""{indent}const {var_name} = document.getElementById({element_id});
{indent}if ({var_name}) {{
{indent}  {var_name}.addEventListener("""
            changes_made.append(
                f"Línea ~{content[:match.start()].count(chr(10)) + 1}: {element_id}"
            )
            return replacement

        content = PATTERN.sub(replace_pattern1, content)

        # Fix patrón 2: const x = document.getElementById('id'); x.addEventListener
        def replace_pattern2(match):
            indent = match.group(1)
            var_name = match.group(2)
            element_id = match.group(3)

            replacement = f"""{indent}const {var_name} = document.getElementById({element_id});
{indent}if ({var_name}) {{
{indent}  {var_name}.addEventListener("""
            changes_made.append(
                f"Línea ~{content[:match.start()].count(chr(10)) + 1}: {var_name} ({element_id})"
            )
            return replacement

        content = PATTERN_MULTILINE.sub(replace_pattern2, content)

        # Cerrar los if que agregamos
        # Buscar addEventListener que no tengan su } de cierre correspondiente
        # Esto es más complejo, mejor hacerlo manualmente

        if content != original_content:
            # Agregar cierre de llaves donde sea necesario
            # Buscar addEventListener seguido de función y agregar } al final
            content = re.sub(
                r"(addEventListener\s*\([^)]+\)\s*\{[^}]*\})\s*(?=\n\s*(?:const|document|if|function|\}))",
                r"\1\n    }\n",
                content,
                flags=re.MULTILINE | re.DOTALL,
            )

            return content, changes_made

        return None, []

    except Exception as e:
        print(f"Error procesando {file_path}: {e}")
        return None, []


def main():
    """Busca y corrige archivos con problemas"""
    base_dir = Path(__file__).parent.parent

    # Directorios a buscar
    search_dirs = [
        base_dir / "templates",
        base_dir / "static" / "js",
    ]

    files_fixed = []
    total_changes = 0

    for search_dir in search_dirs:
        if not search_dir.exists():
            continue

        # Buscar archivos HTML y JS
        for ext in ["*.html", "*.js"]:
            for file_path in search_dir.rglob(ext):
                # Saltar node_modules y otros
                if "node_modules" in str(file_path) or "venv" in str(file_path):
                    continue

                fixed_content, changes = fix_javascript_file(file_path)

                if fixed_content:
                    # Crear backup
                    backup_path = file_path.with_suffix(file_path.suffix + ".backup")
                    with open(file_path, "r", encoding="utf-8") as f:
                        with open(backup_path, "w", encoding="utf-8") as b:
                            b.write(f.read())

                    # Escribir archivo corregido
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(fixed_content)

                    files_fixed.append(str(file_path))
                    total_changes += len(changes)
                    print(f"✅ Corregido: {file_path}")
                    for change in changes:
                        print(f"   - {change}")

    print(f"\n📊 Resumen:")
    print(f"   Archivos corregidos: {len(files_fixed)}")
    print(f"   Cambios totales: {total_changes}")

    if files_fixed:
        print(f"\n⚠️  Se crearon backups (.backup) de los archivos originales")
        print(f"   Revisa los cambios antes de commitear")


if __name__ == "__main__":
    main()
