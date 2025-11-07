#!/usr/bin/env python3
"""
Script para verificar referencias a archivos estáticos en templates
Después de la limpieza de producción, busca referencias a archivos eliminados
"""

import os
import re
import sys
from pathlib import Path

def find_static_references(templates_dir, static_dir):
    """Busca referencias a archivos estáticos en templates"""
    
    # Archivos que fueron eliminados
    deleted_files = [
        'fondo_interactivo.d41d8cd9.js',
        'particles.json',
        'fondo_futurista.mp4',
        'coverage_html_cb_497bf287.5d92da3d.js',
        'playwright.config.92b72f4a.js',
        'postcss.config.854b3875.js',
        'setupTests.1a77571e.js',
        'reportWebVitals.240e2381.js',
        'test_busqueda_repuestos_frontend.spec.cdadc038.js',
        'test_busqueda_servicios_frontend.spec.ce63f330.js',
        'test_formulario_documento_completo.spec.0d6a0b0e.js',
        'documentos_form_enhanced.3925c684.js',
        'documentos_form_new.ddc7a38e.js',
        'documentos_form_numbers.5b6b1df0.js',
        'documentos_form_patch.dda4d38d.js',
        'documentos_form_v8.09ba7993.js',
        'documento_form_advanced.37409a73.js',
        'documento_form_futurista.41d935d3.js',
        'formulario_documento.f8cbd4aa.js',
        'TallerPro_logo.eda79c86.png',
        'select2_custom.e65898ee.css',
        'jquery-ui.min.c6b0df13.js'
    ]
    
    # Archivos que fueron renombrados
    renamed_files = {
        'autocomplete.init.ce7877f2.js': 'autocomplete.init.js',
        'documentos_form_final.9b337ae4.js': 'documentos_form.js',
        'style.c6dfc145.css': 'app.min.css'
    }
    
    issues = []
    
    # Buscar en templates
    for template_file in Path(templates_dir).rglob('*.html'):
        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Buscar referencias a archivos eliminados
            for deleted_file in deleted_files:
                if deleted_file in content:
                    issues.append({
                        'type': 'deleted_reference',
                        'file': str(template_file),
                        'issue': f'Referencia a archivo eliminado: {deleted_file}',
                        'severity': 'error'
                    })
            
            # Buscar referencias a archivos renombrados
            for old_name, new_name in renamed_files.items():
                if old_name in content:
                    issues.append({
                        'type': 'renamed_reference',
                        'file': str(template_file),
                        'issue': f'Referencia a archivo renombrado: {old_name} -> {new_name}',
                        'severity': 'warning'
                    })
                    
        except Exception as e:
            issues.append({
                'type': 'read_error',
                'file': str(template_file),
                'issue': f'Error leyendo archivo: {e}',
                'severity': 'error'
            })
    
    return issues

def main():
    if len(sys.argv) != 3:
        print("Uso: python verify_template_references.py <templates_dir> <static_dir>")
        sys.exit(1)
    
    templates_dir = sys.argv[1]
    static_dir = sys.argv[2]
    
    print("VERIFICACION DE REFERENCIAS EN TEMPLATES")
    print("=======================================")
    print(f"Templates: {templates_dir}")
    print(f"Static: {static_dir}")
    print()
    
    issues = find_static_references(templates_dir, static_dir)
    
    if not issues:
        print("✅ No se encontraron referencias problemáticas")
        return
    
    # Agrupar por severidad
    errors = [i for i in issues if i['severity'] == 'error']
    warnings = [i for i in issues if i['severity'] == 'warning']
    
    if errors:
        print(f"❌ ERRORES ({len(errors)}):")
        for issue in errors:
            print(f"  {issue['file']}: {issue['issue']}")
        print()
    
    if warnings:
        print(f"⚠️  ADVERTENCIAS ({len(warnings)}):")
        for issue in warnings:
            print(f"  {issue['file']}: {issue['issue']}")
        print()
    
    print(f"Total: {len(issues)} problemas encontrados")
    
    if errors:
        sys.exit(1)

if __name__ == '__main__':
    main()
