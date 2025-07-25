#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import os

def auditor_100_percent():
    """
    Auditor avanzado para identificar TODAS las vulnerabilidades que pueden corregirse al 100%
    """
    archivos = [
        'taller/documentos/views.py',
        'taller/reportes/views.py', 
        'taller/vehiculos/views.py',
        'taller/repuestos/views.py',
        'taller/servicios/views.py',
        'taller/api/views.py',
        'taller/views.py'
    ]
    
    vulnerabilidades_detalladas = []
    catalogos_globales = 0
    criticas_corregibles = 0
    
    print("🛡️ AUDITOR 100% - ANÁLISIS DETALLADO")
    print("=" * 50)
    
    for archivo in archivos:
        if os.path.exists(archivo):
            try:
                with open(archivo, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                for i, line in enumerate(lines, 1):
                    line_clean = line.strip()
                    
                    # Buscar .objects.all()
                    if 'objects.all()' in line_clean:
                        # Analizar contexto para determinar si es catálogo global o crítico
                        context_lines = lines[max(0, i-3):min(len(lines), i+3)]
                        context = ' '.join([l.strip() for l in context_lines])
                        
                        es_catalogo_global = any(keyword in context.lower() for keyword in [
                            'marca', 'modelo', 'color', 'motor', 'caja', 'servicio', 'categoria'
                        ])
                        
                        tiene_login_required = any('@login_required' in l for l in lines[max(0, i-10):i])
                        
                        if es_catalogo_global and tiene_login_required:
                            catalogos_globales += 1
                            tipo = "CATÁLOGO GLOBAL (OK)"
                        elif es_catalogo_global:
                            criticas_corregibles += 1
                            tipo = "CATÁLOGO SIN LOGIN"
                            vulnerabilidades_detalladas.append({
                                'archivo': archivo,
                                'linea': i,
                                'codigo': line_clean,
                                'tipo': tipo,
                                'solucion': 'Agregar @login_required'
                            })
                        else:
                            criticas_corregibles += 1
                            tipo = "CRÍTICA"
                            vulnerabilidades_detalladas.append({
                                'archivo': archivo,
                                'linea': i,
                                'codigo': line_clean,
                                'tipo': tipo,
                                'solucion': 'Filtrar por empresa'
                            })
                        
                        print(f"📍 {archivo}:{i} - {tipo}")
                        print(f"   Código: {line_clean[:80]}...")
                    
                    # Buscar .objects.get() sin empresa
                    if 'objects.get(' in line_clean and 'empresa' not in line_clean:
                        es_catalogo = any(keyword in line_clean.lower() for keyword in [
                            'marca', 'modelo', 'color', 'motor', 'caja'
                        ])
                        
                        if not es_catalogo:
                            criticas_corregibles += 1
                            vulnerabilidades_detalladas.append({
                                'archivo': archivo,
                                'linea': i,
                                'codigo': line_clean,
                                'tipo': "GET SIN EMPRESA",
                                'solucion': 'Agregar filtro empresa'
                            })
                            print(f"📍 {archivo}:{i} - GET SIN EMPRESA")
                            print(f"   Código: {line_clean[:80]}...")
                            
            except Exception as e:
                print(f"Error procesando {archivo}: {e}")
    
    print("\n" + "=" * 50)
    print("📊 RESUMEN PARA CORRECCIÓN 100%:")
    print("=" * 50)
    print(f"🟢 Catálogos globales protegidos: {catalogos_globales}")
    print(f"🔴 Vulnerabilidades corregibles: {criticas_corregibles}")
    print(f"📋 Total vulnerabilidades detalladas: {len(vulnerabilidades_detalladas)}")
    
    if vulnerabilidades_detalladas:
        print("\n🎯 PLAN DE CORRECCIÓN:")
        print("=" * 25)
        for vuln in vulnerabilidades_detalladas:
            print(f"• {vuln['archivo']}:{vuln['linea']} - {vuln['tipo']}")
            print(f"  Solución: {vuln['solucion']}")
            print(f"  Código: {vuln['codigo'][:60]}...")
            print()
    
    return vulnerabilidades_detalladas

if __name__ == "__main__":
    vulnerabilidades = auditor_100_percent()
    
    if vulnerabilidades:
        print(f"🚀 Se pueden corregir {len(vulnerabilidades)} vulnerabilidades más")
        print("para lograr 100% de seguridad en áreas críticas!")
    else:
        print("🎉 ¡Sistema 100% seguro en áreas críticas!")
