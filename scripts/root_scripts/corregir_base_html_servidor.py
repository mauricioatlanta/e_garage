#!/usr/bin/env python
"""
Script para corregir la estructura rota de templates/common/base.html en el servidor
Corrige los tags {% if %} sin cerrar y elimina código duplicado
"""
import os
import shutil
import time

file_path = "/home/atlantareciclajes/apps/egarage/releases/2025-11-17_1615_eg/templates/common/base.html"

print("=" * 70)
print("CORRIGIENDO templates/common/base.html EN EL SERVIDOR")
print("=" * 70)

# Crear backup
if os.path.exists(file_path):
    backup_path = file_path + ".bak_" + str(int(time.time()))
    shutil.copy2(file_path, backup_path)
    print(f"✅ Backup creado: {backup_path}")

# Leer el archivo actual
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"📄 Archivo leído: {len(lines)} líneas")

# Buscar la sección problemática (alrededor de la línea 175-190)
new_lines = []
i = 0
fixed = False

while i < len(lines):
    line = lines[i]
    line_num = i + 1
    
    # Buscar el inicio del header (línea ~175)
    if '{% if request.path != "/cl/" and request.path != "/us/" %}' in line:
        new_lines.append(line)
        i += 1
        
        # Siguiente línea debe ser el header
        if i < len(lines) and '<header class="company-header' in lines[i]:
            new_lines.append(lines[i])
            i += 1
            
            # Ahora viene la sección del logo que puede estar rota
            # Buscar el patrón correcto
            if i < len(lines) and '{% if company_logo_url or COMPANY_LOGO %}' in lines[i]:
                new_lines.append(lines[i])
                i += 1
                
                # Buscar el if interno
                if i < len(lines) and "{% if '/static/images/' not in" in lines[i]:
                    new_lines.append(lines[i])
                    i += 1
                    
                    # Leer hasta encontrar el {% endif %} del if interno
                    while i < len(lines):
                        if '{% endif %}' in lines[i]:
                            new_lines.append(lines[i])
                            i += 1
                            break
                        else:
                            new_lines.append(lines[i])
                            i += 1
                    
                    # Ahora debe venir el {% endif %} del if externo
                    if i < len(lines) and '{% endif %}' in lines[i]:
                        new_lines.append(lines[i])
                        i += 1
                        fixed = True
                        print(f"✅ Estructura corregida alrededor de la línea {line_num}")
                    else:
                        # Agregar el endif faltante
                        new_lines.append("  {% endif %}\n")
                        print(f"✅ Agregado {% endif %} faltante después de la línea {i}")
                        fixed = True
                else:
                    # No hay if interno, solo cerrar el if externo
                    # Leer hasta encontrar el endif o agregarlo
                    found_endif = False
                    while i < len(lines) and i < line_num + 20:  # Buscar en las próximas 20 líneas
                        if '{% endif %}' in lines[i]:
                            new_lines.append(lines[i])
                            i += 1
                            found_endif = True
                            break
                        elif '<div class="flex flex-col">' in lines[i]:
                            # Llegamos al div del título, agregar endif antes
                            new_lines.append("  {% endif %}\n")
                            new_lines.append(lines[i])
                            i += 1
                            found_endif = True
                            fixed = True
                            break
                        else:
                            new_lines.append(lines[i])
                            i += 1
                    
                    if not found_endif:
                        new_lines.append("  {% endif %}\n")
                        fixed = True
            else:
                # No hay if de company_logo_url, continuar normalmente
                new_lines.append(line)
                i += 1
        else:
            new_lines.append(line)
            i += 1
    else:
        new_lines.append(line)
        i += 1

# Escribir el archivo corregido
with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"\n✅ Archivo corregido: {file_path}")
print(f"✅ Líneas totales: {len(new_lines)}")

# Verificar que la estructura esté correcta
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()
    
    # Contar ifs y endifs en la sección del header
    if_count = content.count('{% if company_logo_url or COMPANY_LOGO %}')
    endif_count = content.count('{% endif %}')
    
    print(f"✅ Verificación: {if_count} if(s) de logo encontrado(s)")
    
    # Verificar que no haya código duplicado problemático
    if '🏢' not in content:
        print("✅ Verificación: Emoji del edificio no encontrado")
    if '🌼 AZUL' not in content:
        print("✅ Verificación: Flor azul no encontrada")
    
    # Verificar estructura básica
    if '{% if company_logo_url or COMPANY_LOGO %}' in content:
        if '{% endif %}' in content[content.find('{% if company_logo_url or COMPANY_LOGO %}'):]:
            print("✅ Verificación: Estructura de if/endif parece correcta")
        else:
            print("⚠️  Advertencia: Puede haber un problema con la estructura")

print("\n⚠️  IMPORTANTE: Reinicia el servidor Django/uWSGI para que los cambios surtan efecto")
print("   Ejecuta: touch /var/www/atlantareciclajes_digitalocean_com_wsgi.py")
print("=" * 70)

