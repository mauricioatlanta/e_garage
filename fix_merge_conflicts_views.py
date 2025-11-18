#!/usr/bin/env python3
"""
Script para eliminar marcadores de conflicto de merge en taller/documentos/views.py
"""
import sys
import re

file_path = "taller/documentos/views.py"

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Detectar marcadores de conflicto
    conflict_markers = [
        r'^<<<<<<<.*?$',
        r'^=======.*?$',
        r'^>>>>>>>.*?$',
        r'^<<<<<<< Updated upstream.*?$',
        r'^=======.*?$',
        r'^>>>>>>> Stashed changes.*?$',
    ]
    
    lines = content.split('\n')
    new_lines = []
    in_conflict = False
    conflict_start = None
    
    for i, line in enumerate(lines, 1):
        # Detectar inicio de conflicto
        if re.match(r'^<<<<<<<', line):
            in_conflict = True
            conflict_start = i
            print(f"⚠️  Marcador de conflicto encontrado en línea {i}: {line[:50]}")
            continue
        
        # Detectar separador de conflicto
        if in_conflict and re.match(r'^=======', line):
            print(f"⚠️  Separador de conflicto en línea {i}")
            continue
        
        # Detectar fin de conflicto
        if in_conflict and re.match(r'^>>>>>>>', line):
            print(f"⚠️  Fin de conflicto en línea {i}: {line[:50]}")
            in_conflict = False
            conflict_start = None
            continue
        
        # Si no estamos en conflicto, agregar la línea
        if not in_conflict:
            new_lines.append(line)
    
    if conflict_start:
        print(f"❌ Conflicto no resuelto que comenzó en línea {conflict_start}")
        sys.exit(1)
    
    new_content = '\n'.join(new_lines)
    
    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"✅ Archivo limpiado. Se eliminaron {len(lines) - len(new_lines)} líneas de conflicto.")
    else:
        print("✅ No se encontraron marcadores de conflicto.")
    
    # Verificar sintaxis
    try:
        compile(new_content, file_path, 'exec')
        print("✅ Sintaxis Python válida.")
    except SyntaxError as e:
        print(f"❌ Error de sintaxis: {e}")
        sys.exit(1)
        
except FileNotFoundError:
    print(f"❌ Archivo no encontrado: {file_path}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

