#!/bin/bash
# Script simple para copiar el template de bienvenida de Colombia al servidor
# Si no existe, copia el de Chile como base

cd /home/atlantareciclajes/apps/egarage/current && \
python3 << 'PYEOF'
import os
import shutil

# Rutas
template_dir = "templates/onboarding"
colombia_template = os.path.join(template_dir, "bienvenida_colombia.html")
chile_template = os.path.join(template_dir, "bienvenida_chile.html")

# Asegurar que el directorio existe
os.makedirs(template_dir, exist_ok=True)

# Si el template de Colombia no existe, copiar el de Chile y reemplazar texto
if not os.path.exists(colombia_template):
    if os.path.exists(chile_template):
        print("📋 Copiando template de Chile como base...")
        shutil.copy(chile_template, colombia_template)
        
        # Leer y reemplazar contenido
        with open(colombia_template, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Reemplazar referencias de Chile por Colombia
        content = content.replace('Chile', 'Colombia')
        content = content.replace('chile', 'colombia')
        content = content.replace('CL', 'CO')
        content = content.replace('/cl/', '/co/')
        content = content.replace('country=CL', 'country=CO')
        content = content.replace('Bogotá, Medellín, Cali y toda Colombia', 'Bogotá, Medellín, Cali y toda Colombia')
        
        # Escribir el archivo modificado
        with open(colombia_template, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Template creado en: {colombia_template}")
    else:
        print(f"❌ No se encontró el template de Chile en: {chile_template}")
        print("⚠️  Necesitas crear el template manualmente o copiarlo desde tu PC local")
else:
    print(f"✅ Template de Colombia ya existe en: {colombia_template}")

# Verificar que el archivo existe
if os.path.exists(colombia_template):
    size = os.path.getsize(colombia_template)
    print(f"✅ Archivo verificado: {size} bytes")
else:
    print(f"❌ El archivo no se pudo crear en: {colombia_template}")

PYEOF

# Reiniciar el servidor
touch /var/www/www_egarage_cl_wsgi.py && \
echo "✅ Script ejecutado y servidor reiniciado"

