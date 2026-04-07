#!/usr/bin/env python
"""
Script para limpiar el archivo urls.py y dejar solo una instancia de la URL de prueba
"""

import re

# Leer el archivo urls.py
with open("gestion_taller/urls.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Eliminar duplicados de la URL de prueba
# Buscar todas las ocurrencias del patrón
pattern = r'    path\("test-doc/", crear_documento_test, name="test_document_form"\),\n    # URL de prueba para el formulario de documento\n    path\("test-doc/", crear_documento_test, name="test_document_form"\),\n    # URL de prueba para el formulario de documento\n    path\("test-doc/", crear_documento_test, name="test_document_form"\),'
replacement = '    # URL de prueba para el formulario de documento\n    path("test-doc/", crear_documento_test, name="test_document_form"),'

content = re.sub(pattern, replacement, content)

# 2. Asegurarse de que la importación esté correcta
# Buscar la línea con la importación
import_pattern = r"from taller\.views\.country_aware_auth import country_aware_login\nfrom taller\.views import crear_documento_test\n"
if import_pattern in content:
    print("OK: Importacion encontrada y correcta")
else:
    # Buscar si está en otra forma
    if "from taller.views import crear_documento_test" in content:
        print("OK: Importacion encontrada")
    else:
        print("ERROR: Importacion no encontrada")

# 3. Escribir el archivo limpio
with open("gestion_taller/urls.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Archivo limpiado exitosamente!")

# Verificar el resultado
print("\\nVerificando resultado...")
with open("gestion_taller/urls.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

count = 0
for i, line in enumerate(lines):
    if "test-doc" in line:
        count += 1
        print(f"Linea {i+1}: {line.rstrip()}")

print(f'\\nTotal de ocurrencias de "test-doc": {count}')
