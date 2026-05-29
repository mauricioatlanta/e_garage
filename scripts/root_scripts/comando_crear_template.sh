#!/bin/bash
# Comando para crear el template directamente en el servidor

cd /home/atlantareciclajes/apps/egarage/releases/2025-11-17_1615_eg
mkdir -p templates/taller/us/en/settings

python3 << 'PYTHON_SCRIPT'
import os

template_dir = "/home/atlantareciclajes/apps/egarage/releases/2025-11-17_1615_eg/templates/taller/us/en/settings"
template_path = os.path.join(template_dir, "futuristic_company_settings.html")

# Leer el contenido desde stdin o usar el contenido completo
# Como el archivo es muy largo, lo mejor es usar heredoc o copiarlo directamente

print("Creando directorio...")
os.makedirs(template_dir, exist_ok=True)

print("NOTA: Este script necesita el contenido completo del template.")
print("Por favor, usa uno de estos métodos:")
print("1. Copiar el archivo desde tu PC usando scp")
print("2. Usar cat con heredoc (ver instrucciones)")
print("3. Usar nano/vim para pegar el contenido")

PYTHON_SCRIPT

