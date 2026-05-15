#!/usr/bin/env python3
"""
Script para eliminar AccountMiddleware de los archivos de settings en el servidor
si el middleware no existe.
"""
import os
import re


def remove_middleware_from_file(file_path):
    """Elimina AccountMiddleware de un archivo de settings."""
    if not os.path.exists(file_path):
        return False

    print(f"📄 Procesando {file_path}...")

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        lines = content.split("\n")

    new_lines = []
    modified = False
    i = 0

    while i < len(lines):
        line = lines[i]

        # Detectar si esta línea contiene AccountMiddleware directamente en MIDDLEWARE
        if '"allauth.account.middleware.AccountMiddleware"' in line:
            print(f"  ❌ Eliminando línea {i+1}: {line.strip()[:60]}...")
            modified = True
            i += 1
            continue

        # Detectar bloque try/except que intenta agregar AccountMiddleware
        if "Agregar AccountMiddleware" in line or ("try:" in line and i + 5 < len(lines)):
            # Verificar si las siguientes líneas contienen AccountMiddleware
            look_ahead = "\n".join(lines[i : min(i + 20, len(lines))])
            if "AccountMiddleware" in look_ahead and (
                "import" in look_ahead or "MIDDLEWARE.insert" in look_ahead
            ):
                # Encontrar el bloque completo try/except
                try_start = i
                try_end = i
                indent = len(line) - len(line.lstrip())

                # Buscar el except correspondiente
                j = i + 1
                while j < len(lines) and j < i + 25:
                    current_line = lines[j]
                    current_indent = len(current_line) - len(current_line.lstrip())

                    if "except" in current_line and current_indent == indent:
                        # Buscar el pass
                        k = j + 1
                        while k < len(lines) and k < j + 5:
                            if (
                                "pass" in lines[k]
                                and len(lines[k]) - len(lines[k].lstrip()) == indent
                            ):
                                try_end = k
                                print(
                                    f"  ❌ Eliminando bloque try/except (líneas {try_start+1}-{try_end+1})"
                                )
                                modified = True
                                i = k + 1
                                break
                            k += 1
                        break
                    j += 1

                if i == try_start:  # No encontramos el except, continuar normalmente
                    new_lines.append(line)
                    i += 1
                continue

        new_lines.append(line)
        i += 1

    if modified:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(new_lines))
        print(f"  ✅ {file_path} corregido")
        return True
    else:
        print(f"  ℹ️  {file_path} no necesita corrección")
        return False


if __name__ == "__main__":
    files = [
        "gestion_taller/settings.py",
        "gestion_taller/settings/base.py",
        "gestion_taller/compacto/settings.py",
    ]

    any_modified = False
    for file_path in files:
        if remove_middleware_from_file(file_path):
            any_modified = True

    if any_modified:
        print("\n✅ Archivos corregidos")
    else:
        print("\nℹ️  No se necesitaron correcciones")
