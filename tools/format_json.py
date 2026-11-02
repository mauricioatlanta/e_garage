#!/usr/bin/env python3
"""
Herramienta para validar y formatear archivos JSON.
"""

import json
import pathlib
import sys


def main():
    bad = []
    formatted_count = 0

    for p in pathlib.Path(".").rglob("*.json"):
        if any(part in p.parts for part in (".venv", "node_modules", "__pycache__")):
            continue
        try:
            content = p.read_text(encoding="utf-8")
            obj = json.loads(content)

            # Formatear el JSON
            formatted = json.dumps(obj, ensure_ascii=False, indent=2) + "\n"

            # Solo escribir si el contenido cambió
            if content != formatted:
                p.write_text(formatted, encoding="utf-8")
                formatted_count += 1
                print(f"✅ Formateado: {p}")

        except json.JSONDecodeError as e:
            bad.append((p, f"JSON inválido: {e}"))
        except Exception as e:
            bad.append((p, f"Error: {e}"))

    if bad:
        print("\n❌ JSON inválidos:")
        for p, msg in bad:
            print(f"  {p} -> {msg}")
        sys.exit(1)
    else:
        if formatted_count > 0:
            print(f"\n✅ OK: {formatted_count} archivos JSON formateados.")
        else:
            print("\n✅ OK: Todos los archivos JSON ya están bien formateados.")


if __name__ == "__main__":
    main()
