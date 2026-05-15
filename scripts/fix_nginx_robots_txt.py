#!/usr/bin/env python3
"""
Script para corregir el bloque robots.txt en nginx
Ejecutar: sudo python3 scripts/fix_nginx_robots_txt.py
"""

import re
import sys
import shutil
from datetime import datetime

CONFIG_FILE = "/etc/nginx/sites-available/egarage"


def main():
    # Verificar que el archivo existe
    try:
        with open(CONFIG_FILE, "r") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"❌ Error: No se encontró {CONFIG_FILE}")
        sys.exit(1)
    except PermissionError:
        print(f"❌ Error: No tienes permisos para leer {CONFIG_FILE}")
        print("   Ejecuta con sudo")
        sys.exit(1)

    print(f"✅ Archivo encontrado: {CONFIG_FILE}")

    # Crear backup
    backup_file = f"{CONFIG_FILE}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(CONFIG_FILE, backup_file)
    print(f"📦 Backup creado: {backup_file}")

    # Patrón para encontrar el bloque robots.txt
    # Busca desde "location = /robots.txt {" hasta el cierre "}"
    # Maneja espacios y saltos de línea
    pattern = r"location\s*=\s*/robots\.txt\s*\{[^}]*\}"

    # Nueva configuración
    new_block = """    location = /robots.txt {
        default_type text/plain;
        alias /srv/egarage/staticfiles/robots.txt;
        access_log off;
        log_not_found off;
    }"""

    # Verificar si existe el bloque
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)

    if match:
        print("✅ Bloque robots.txt encontrado, actualizando...")
        # Reemplazar el bloque
        content = re.sub(pattern, new_block, content, flags=re.MULTILINE | re.DOTALL)
    else:
        print("⚠️  Bloque robots.txt no encontrado, agregando...")
        # Intentar agregar después de location /static/
        if "location /static/" in content:
            # Buscar el final del bloque /static/ y agregar después
            static_pattern = r"(location /static/[^}]*\})"
            replacement = r"\1\n\n    location = /robots.txt {\n        default_type text/plain;\n        alias /srv/egarage/staticfiles/robots.txt;\n        access_log off;\n        log_not_found off;\n    }"
            content = re.sub(static_pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)
            print("✅ Bloque agregado después de location /static/")
        else:
            # Agregar antes del cierre del último server block
            # Buscar el último "}" que cierra un server block
            # (asumiendo que está al final del archivo o después de location /)
            if "location / {" in content:
                # Agregar antes del cierre del server block
                content = re.sub(
                    r"(\n\s*)\}(?=\s*$)",
                    r"\1    location = /robots.txt {\n        default_type text/plain;\n        alias /srv/egarage/staticfiles/robots.txt;\n        access_log off;\n        log_not_found off;\n    }\n\1}",
                    content,
                    count=1,
                )
                print("✅ Bloque agregado antes del cierre del server block")
            else:
                print("❌ No se pudo determinar dónde agregar el bloque")
                print("   Por favor, agrega manualmente el bloque después de location /static/")
                sys.exit(1)

    # Escribir el archivo modificado
    try:
        with open(CONFIG_FILE, "w") as f:
            f.write(content)
        print("✅ Archivo actualizado")
    except PermissionError:
        print(f"❌ Error: No tienes permisos para escribir en {CONFIG_FILE}")
        print("   Ejecuta con sudo")
        sys.exit(1)

    print("\n" + "=" * 50)
    print("Verificando sintaxis de nginx...")
    print("=" * 50)

    # Verificar sintaxis (requiere sudo)
    import subprocess

    result = subprocess.run(["nginx", "-t"], capture_output=True, text=True)

    if result.returncode == 0:
        print("✅ Sintaxis de nginx correcta")
        print("\n" + "=" * 50)
        print("Próximos pasos:")
        print("=" * 50)
        print("1. Recargar nginx:")
        print("   sudo systemctl reload nginx")
        print("\n2. Verificar robots.txt:")
        print("   curl -i https://egarage.cl/robots.txt | head -n 20")
        print("\nDeberías ver HTTP/2 200 y el contenido del archivo.")
    else:
        print("❌ Error en la sintaxis de nginx:")
        print(result.stderr)
        print("\nRestaurando backup...")
        shutil.copy2(backup_file, CONFIG_FILE)
        print(f"✅ Backup restaurado desde: {backup_file}")
        sys.exit(1)


if __name__ == "__main__":
    main()
