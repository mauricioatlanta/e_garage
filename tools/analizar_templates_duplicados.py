#!/usr/bin/env python
"""
Script para analizar templates duplicados entre /templates/ y /taller/templates/
"""

import difflib
import os
from pathlib import Path

# Directorios a comparar
TEMPLATES_MAIN = Path("templates")
TEMPLATES_TALLER = Path("taller/templates")


def get_relative_path(file_path, base_path):
    """Obtiene ruta relativa desde base"""
    return file_path.relative_to(base_path)


def find_templates(base_path):
    """Encuentra todos los archivos .html en un directorio"""
    templates = {}
    for file_path in base_path.rglob("*.html"):
        rel_path = get_relative_path(file_path, base_path)
        templates[str(rel_path)] = file_path
    return templates


def compare_files(file1, file2):
    """Compara dos archivos y retorna si son idénticos"""
    try:
        with open(file1, encoding="utf-8") as f1:
            content1 = f1.read()
        with open(file2, encoding="utf-8") as f2:
            content2 = f2.read()

        if content1 == content2:
            return "IDÉNTICOS", 1.0
        else:
            # Calcular similitud
            ratio = difflib.SequenceMatcher(None, content1, content2).ratio()
            return "DIFERENTES", ratio
    except Exception as e:
        return f"ERROR: {e}", 0.0


def main():
    print("=" * 80)
    print("ANÁLISIS DE TEMPLATES DUPLICADOS - eGarage")
    print("=" * 80)
    print()

    # Encontrar todos los templates
    print("📁 Buscando templates en /templates/...")
    templates_main = find_templates(TEMPLATES_MAIN)
    print(f"   Encontrados: {len(templates_main)} archivos")

    print("📁 Buscando templates en /taller/templates/...")
    templates_taller = find_templates(TEMPLATES_TALLER)
    print(f"   Encontrados: {len(templates_taller)} archivos")
    print()

    # Buscar duplicados potenciales
    print("🔍 Buscando duplicados potenciales...")
    print()

    duplicados = []
    templates_unicos_taller = []

    for rel_path, taller_file in templates_taller.items():
        # Buscar si existe en templates principales
        # Primero buscar con la ruta exacta
        if rel_path in templates_main:
            main_file = templates_main[rel_path]
            status, similarity = compare_files(main_file, taller_file)
            duplicados.append(
                {
                    "rel_path": rel_path,
                    "main_file": main_file,
                    "taller_file": taller_file,
                    "status": status,
                    "similarity": similarity,
                }
            )
        else:
            # Buscar sin el prefijo "taller/" si existe
            if rel_path.startswith("taller/"):
                alt_path = rel_path[7:]  # Remover "taller/"
                if alt_path in templates_main:
                    main_file = templates_main[alt_path]
                    status, similarity = compare_files(main_file, taller_file)
                    duplicados.append(
                        {
                            "rel_path": rel_path,
                            "alt_path": alt_path,
                            "main_file": main_file,
                            "taller_file": taller_file,
                            "status": status,
                            "similarity": similarity,
                        }
                    )
                else:
                    templates_unicos_taller.append(
                        {"rel_path": rel_path, "file": taller_file}
                    )
            else:
                templates_unicos_taller.append(
                    {"rel_path": rel_path, "file": taller_file}
                )

    # Reportar resultados
    print("=" * 80)
    print("RESULTADOS DEL ANÁLISIS")
    print("=" * 80)
    print()

    if duplicados:
        print(f"⚠️  DUPLICADOS ENCONTRADOS: {len(duplicados)}")
        print()

        identicos = [d for d in duplicados if d["status"] == "IDÉNTICOS"]
        diferentes = [d for d in duplicados if d["status"] == "DIFERENTES"]

        if identicos:
            print(f"✅ Archivos IDÉNTICOS ({len(identicos)}):")
            print("   (Pueden ser eliminados de taller/templates)")
            print()
            for dup in identicos:
                print(f"   - {dup['rel_path']}")
                print(f"     /templates/{dup.get('alt_path', dup['rel_path'])}")
                print(f"     /taller/templates/{dup['rel_path']}")
                print()

        if diferentes:
            print(f"⚠️  Archivos DIFERENTES con mismo nombre ({len(diferentes)}):")
            print("   (Requieren revisión manual)")
            print()
            for dup in diferentes:
                print(f"   - {dup['rel_path']}")
                print(f"     Similitud: {dup['similarity']*100:.1f}%")
                print(f"     /templates/{dup.get('alt_path', dup['rel_path'])}")
                print(f"     /taller/templates/{dup['rel_path']}")
                print()

    if templates_unicos_taller:
        print(
            f"📝 TEMPLATES ÚNICOS en taller/templates/ ({len(templates_unicos_taller)}):"
        )
        print("   (Deben moverse a /templates/)")
        print()
        for tmpl in templates_unicos_taller:
            print(f"   - {tmpl['rel_path']}")
        print()

    # Guardar reporte
    report_path = Path("docs/TEMPLATES_DUPLICADOS_REPORTE.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Reporte de Templates Duplicados - eGarage\n\n")
        f.write(f"**Fecha:** {os.popen('date').read().strip()}\n\n")
        f.write("## Resumen\n\n")
        f.write(f"- Templates en /templates/: {len(templates_main)}\n")
        f.write(f"- Templates en /taller/templates/: {len(templates_taller)}\n")
        f.write(f"- Duplicados encontrados: {len(duplicados)}\n")
        f.write(f"- Templates únicos en taller/: {len(templates_unicos_taller)}\n\n")

        if identicos:
            f.write("## Archivos Idénticos\n\n")
            f.write(
                "Estos archivos pueden ser eliminados de taller/templates/ de forma segura:\n\n"
            )
            for dup in identicos:
                f.write(f"- `{dup['rel_path']}`\n")
            f.write("\n")

        if diferentes:
            f.write("## Archivos Diferentes (Requieren Revisión)\n\n")
            for dup in diferentes:
                f.write(f"### {dup['rel_path']}\n\n")
                f.write(f"- **Similitud:** {dup['similarity']*100:.1f}%\n")
                f.write(
                    f"- **Ubicación 1:** `/templates/{dup.get('alt_path', dup['rel_path'])}`\n"
                )
                f.write(f"- **Ubicación 2:** `/taller/templates/{dup['rel_path']}`\n")
                f.write("- **Acción:** Revisar manualmente y consolidar\n\n")

        if templates_unicos_taller:
            f.write("## Templates Únicos (Para Mover)\n\n")
            f.write(
                "Estos templates deben moverse de /taller/templates/ a /templates/:\n\n"
            )
            for tmpl in templates_unicos_taller:
                f.write(f"- `{tmpl['rel_path']}`\n")
            f.write("\n")

    print(f"📄 Reporte guardado en: {report_path}")
    print()
    print("=" * 80)
    print("ANÁLISIS COMPLETADO")
    print("=" * 80)


if __name__ == "__main__":
    main()
