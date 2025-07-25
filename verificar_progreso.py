#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import os

def verificar_progreso():
    archivos = [
        'taller/documentos/views.py',
        'taller/reportes/views.py', 
        'taller/vehiculos/views.py',
        'taller/repuestos/views.py',
        'taller/servicios/views.py',
        'taller/api/views.py'
    ]
    
    total_objects_all = 0
    total_get_sin_empresa = 0
    
    print("=== VERIFICACION DE PROGRESO DE SEGURIDAD ===")
    
    for archivo in archivos:
        if os.path.exists(archivo):
            try:
                with open(archivo, 'r', encoding='utf-8') as f:
                    contenido = f.read()
                
                # Buscar .objects.all() 
                objects_all = len(re.findall(r'objects\.all\(\)', contenido))
                
                # Buscar .objects.get() sin filtro empresa
                objects_get = len(re.findall(r'objects\.get\([^)]+\)', contenido))
                lineas_get = re.findall(r'.*objects\.get\([^)]+\).*', contenido)
                get_sin_empresa = sum(1 for linea in lineas_get if 'empresa' not in linea)
                
                print(f"\n{archivo}:")
                print(f"  - .objects.all(): {objects_all}")
                print(f"  - .objects.get() sin empresa: {get_sin_empresa}")
                
                total_objects_all += objects_all
                total_get_sin_empresa += get_sin_empresa
                
            except Exception as e:
                print(f"Error procesando {archivo}: {e}")
        else:
            print(f"Archivo no encontrado: {archivo}")
    
    print(f"\n=== RESUMEN ===")
    print(f"Total .objects.all() sin filtros: {total_objects_all}")
    print(f"Total .objects.get() sin empresa: {total_get_sin_empresa}")
    print(f"Vulnerabilidades criticas restantes: {total_objects_all + total_get_sin_empresa}")
    
    if total_objects_all + total_get_sin_empresa < 30:
        print("✅ ¡Excelente progreso! Quedan menos de 30 vulnerabilidades criticas")
    elif total_objects_all + total_get_sin_empresa < 60:
        print("🔄 Buen progreso, quedan menos de 60 vulnerabilidades criticas")
    else:
        print("⚠️ Aun hay trabajo por hacer")

if __name__ == "__main__":
    verificar_progreso()
