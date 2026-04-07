#!/usr/bin/env python
"""
Script para agregar la URL de prueba al archivo urls.py
"""

import re

# Leer el archivo urls.py
with open("gestion_taller/urls.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Agregar la importación de la view
# Buscar donde agregar la importación (después de otras importaciones de taller)
import_pattern = r"from taller\.views\.country_aware_auth import country_aware_login"
match = re.search(import_pattern, content)

if match:
    # Agregar nuestra importación después de esta
    import_line = "from taller.views import crear_documento_test\\n"
    content = content[: match.end()] + "\\n" + import_line + content[match.end() :]

    print("OK: Importacion agregada exitosamente!")
else:
    print("ERROR: No se pudo encontrar donde agregar la importacion")

# 2. Agregar la URL
# Buscar donde agregar la URL (después de las PWA y antes de workspace)
# Buscar la línea con "urlpatterns = ["
pattern = r"urlpatterns = \["
match = re.search(pattern, content)

if match:
    start_pos = match.end()

    # Encontrar el primer path después de urlpatterns
    after_start = content[start_pos:]

    # Insertar nuestra URL después del primer path (que es el de PWA)
    # Buscar el primer cierre de paréntesis después de path
    first_path_end = after_start.find(")") + 1

    if first_path_end > 0:
        # Construir el nuevo contenido
        new_url = """    # URL de prueba para el formulario de documento
    path("test-doc/", crear_documento_test, name="test_document_form"),"""

        # Insertar después del primer path
        new_after_start = (
            after_start[:first_path_end] + "\\n" + new_url + after_start[first_path_end:]
        )
        new_content = content[:start_pos] + new_after_start

        # Escribir el archivo actualizado
        with open("gestion_taller/urls.py", "w", encoding="utf-8") as f:
            f.write(new_content)

        print("OK: URL agregada exitosamente!")
    else:
        print("ERROR: No se pudo encontrar donde insertar la URL")
else:
    print("ERROR: No se encontró urlpatterns en el archivo")
