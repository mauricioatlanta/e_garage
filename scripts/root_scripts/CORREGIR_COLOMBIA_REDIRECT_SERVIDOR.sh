#!/bin/bash
# Script para corregir la redirección de Colombia en el servidor

cd /home/atlantareciclajes/apps/egarage/current && \
python3 << 'PYEOF'
import sys

file_path = "taller/urls_extra/colombia.py"

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Buscar la línea con la redirección y agregar ruta para /co/es/
    found_redirect = False
    found_es_route = False
    
    for i, line in enumerate(lines):
        if 'path("",' in line and 'colombia_home' in ''.join(lines[i:i+2]):
            # Actualizar redirección a /co/es/
            if '/co/egarage/' in ''.join(lines[i:i+3]):
                for j in range(i, min(i+3, len(lines))):
                    if 'HttpResponseRedirect("/co/egarage/")' in lines[j]:
                        lines[j] = lines[j].replace('/co/egarage/', '/co/es/')
                        print(f"✅ Línea {j+1} actualizada: {lines[j].strip()}")
                        found_redirect = True
                        break
            elif '/co/es/' in ''.join(lines[i:i+3]):
                print(f"✅ Redirección ya está correcta en línea {i+1}")
                found_redirect = True
            break
    
    # Buscar si ya existe la ruta "es/"
    for i, line in enumerate(lines):
        if 'path("es/",' in line and 'colombia' in ''.join(lines[i:i+2]):
            found_es_route = True
            print(f"✅ Ruta 'es/' ya existe en línea {i+1}")
            break
    
    # Si no existe la ruta "es/", agregarla después de la ruta raíz
    if not found_es_route and found_redirect:
        for i, line in enumerate(lines):
            if 'path("",' in line and 'colombia_home' in ''.join(lines[i:i+2]):
                # Insertar después de esta línea
                indent = len(line) - len(line.lstrip())
                new_line = ' ' * indent + 'path("es/", lambda request: HttpResponseRedirect("/co/es/egarage/"), name="colombia_es_home"),\n'
                lines.insert(i+1, new_line)
                print(f"✅ Ruta 'es/' agregada después de línea {i+1}")
                break
    else:
        # Si no se encontró, buscar la línea con path("", ...)
        for i, line in enumerate(lines):
            if 'path("",' in line and 'colombia_home' in ''.join(lines[i:i+2]):
                # Buscar la siguiente línea que tenga HttpResponseRedirect
                for j in range(i, min(i+3, len(lines))):
                    if 'HttpResponseRedirect' in lines[j]:
                        if '/co/egarage/' in lines[j]:
                            lines[j] = lines[j].replace('/co/egarage/', '/co/es/')
                            print(f"✅ Línea {j+1} actualizada: {lines[j].strip()}")
                        elif '/co/es/' in lines[j]:
                            print(f"✅ Línea {j+1} ya está correcta: {lines[j].strip()}")
                        break
                break
    
    # Escribir el archivo actualizado
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print("✅ Archivo actualizado correctamente")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

PYEOF

# Reiniciar el servidor
touch /var/www/www_egarage_cl_wsgi.py && \
echo "✅ Cambios aplicados y servidor reiniciado"

