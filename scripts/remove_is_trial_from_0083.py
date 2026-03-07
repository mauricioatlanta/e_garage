#!/usr/bin/env python3
"""
Elimina el bloque AddField(is_trial) de la migración 0083 para evitar DuplicateColumn.
is_trial ya lo maneja 0082_empresa_is_trial_if_not_exists.

IMPORTANTE: Solo se borran las líneas del bloque; NUNCA la coma del elemento anterior,
para no romper la sintaxis de operations = [ ... ].

Uso (en el servidor):
  python scripts/remove_is_trial_from_0083.py /srv/egarage/taller/migrations/0083_alter_documentsequence_unique_together_and_more.py
"""
import re
import sys
import py_compile
from pathlib import Path

# Ruta por defecto (repo local)
DEFAULT_PATH = Path(__file__).resolve().parent.parent / "taller" / "migrations"
DEFAULT_FILE = DEFAULT_PATH / "0083_alter_documentsequence_unique_together_and_more.py"


def main():
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
    else:
        path = DEFAULT_FILE

    if not path.exists():
        print(f"Archivo no encontrado: {path}")
        print("Uso: python remove_is_trial_from_0083.py [ruta/a/0083_....py]")
        sys.exit(1)

    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    out = []
    i = 0
    removed = False

    while i < len(lines):
        line = lines[i]
        # ¿Esta línea inicia el bloque AddField(empresa, is_trial)?
        chunk = "".join(lines[i : min(i + 6, len(lines))])
        if "migrations.AddField(" in line and "empresa" in chunk and "is_trial" in chunk:
            # Borrar solo las líneas del bloque hasta la que cierra "),"
            # NO tocamos la coma del elemento anterior (ya está en out).
            i += 1
            while i < len(lines):
                if re.match(r"^\s*\),\s*$", lines[i].strip()):
                    i += 1
                    removed = True
                    break
                i += 1
            continue
        out.append(line)
        i += 1
    if not removed:
        print("No se encontró el bloque AddField(is_trial). Puede que ya esté eliminado.")
        sys.exit(0)

    new_text = "".join(out)
    path.write_text(new_text, encoding="utf-8")

    # Validar sintaxis sin ejecutar Django
    try:
        py_compile.compile(str(path), doraise=True)
    except py_compile.PyCompileError as e:
        print(f"ERROR: La sintaxis quedó rota. Restaura el archivo y quita is_trial a mano.")
        print(e)
        sys.exit(1)
    print(f"Listo: bloque is_trial eliminado y sintaxis OK: {path}")


if __name__ == "__main__":
    main()
