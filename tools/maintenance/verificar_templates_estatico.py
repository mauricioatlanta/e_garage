#!/usr/bin/env python
"""
Script de verificación estática para la migración de templates.
Verifica que los archivos estén correctamente configurados.
"""

import glob
import os
import re
from pathlib import Path


class StaticTemplateVerifier:
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.results = []
        
    def log(self, message, status="INFO"):
        print(f"[{status}] {message}")
        
    def check_views_use_mixin(self):
        """Verificar que las vistas usen CountryLangTemplateMixin"""
        self.log("🔍 Verificando uso de CountryLangTemplateMixin en vistas...")
        
        view_files = [
            'taller/documentos/views_migrated.py',
            'taller/documentos/views_cbv.py',
            'taller/documentos/views_listado.py',
            'taller/documentos/views_class_based.py'
        ]
        
        for view_file in view_files:
            file_path = self.base_path / view_file
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    if 'CountryLangTemplateMixin' in content:
                        self.log(f"✅ {view_file} - Usa CountryLangTemplateMixin")
                    else:
                        self.log(f"❌ {view_file} - NO usa CountryLangTemplateMixin", "WARNING")
                        
                    # Verificar uso de base_template_name
                    if 'base_template_name' in content:
                        self.log(f"✅ {view_file} - Usa base_template_name")
                    else:
                        self.log(f"❌ {view_file} - NO usa base_template_name", "WARNING")
            else:
                self.log(f"⚠️  {view_file} - Archivo no encontrado", "WARNING")
    
    def check_template_structure(self):
        """Verificar estructura de templates canónicos"""
        self.log("🏗️  Verificando estructura de templates canónicos...")
        
        expected_structure = [
            'templates_canonical/taller/cl/es/documentos/',
            'templates_canonical/taller/cl/en/documentos/',
            'templates_canonical/taller/us/es/documentos/',
            'templates_canonical/taller/us/en/documentos/',
        ]
        
        required_templates = [
            'documento_form.html',
            'lista_documentos.html',
            'ver_documento_nuevo.html',
            'editar_documento_nuevo.html',
            'crear_documento.html',
            'confirmar_eliminar.html'
        ]
        
        for structure_path in expected_structure:
            full_path = self.base_path / structure_path
            if full_path.exists():
                self.log(f"✅ {structure_path} - Directorio existe")
                
                # Verificar templates requeridos
                missing_templates = []
                for template in required_templates:
                    template_path = full_path / template
                    if not template_path.exists():
                        missing_templates.append(template)
                
                if missing_templates:
                    self.log(f"⚠️  {structure_path} - Faltan: {', '.join(missing_templates)}", "WARNING")
                else:
                    self.log(f"✅ {structure_path} - Todos los templates requeridos presentes")
            else:
                self.log(f"❌ {structure_path} - Directorio NO existe", "ERROR")
    
    def check_settings_configuration(self):
        """Verificar configuración en settings.py"""
        self.log("⚙️  Verificando configuración en settings.py...")
        
        settings_path = self.base_path / 'gestion_taller/settings.py'
        if settings_path.exists():
            with open(settings_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                if 'templates_canonical' in content:
                    self.log("✅ settings.py - Configurado para usar templates_canonical")
                else:
                    self.log("❌ settings.py - NO configurado para templates_canonical", "ERROR")
                    
                if 'company_context' in content:
                    self.log("✅ settings.py - Context processor company_context configurado")
                else:
                    self.log("❌ settings.py - Context processor company_context NO configurado", "ERROR")
        else:
            self.log("❌ settings.py - Archivo no encontrado", "ERROR")
    
    def check_urls_updated(self):
        """Verificar que las URLs usen las nuevas vistas"""
        self.log("🔗 Verificando configuración de URLs...")
        
        urls_path = self.base_path / 'taller/documentos/urls.py'
        if urls_path.exists():
            with open(urls_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Verificar imports de nuevas vistas
                if 'views_migrated' in content:
                    self.log("✅ URLs - Importa vistas migradas")
                else:
                    self.log("❌ URLs - NO importa vistas migradas", "WARNING")
                
                # Verificar que no use vistas hardcodeadas
                if 'views_moderno.documento_form' in content:
                    self.log("⚠️  URLs - Aún usa views_moderno.documento_form", "WARNING")
                
                if '.as_view()' in content:
                    self.log("✅ URLs - Usa vistas basadas en clases")
                else:
                    self.log("❌ URLs - NO usa vistas basadas en clases", "WARNING")
        else:
            self.log("❌ URLs - Archivo no encontrado", "ERROR")
    
    def check_old_template_references(self):
        """Buscar referencias a templates antiguos"""
        self.log("🕵️  Buscando referencias a templates antiguos...")
        
        # Buscar en archivos Python
        python_files = glob.glob(str(self.base_path / "**/*.py"), recursive=True)
        old_templates = [
            'crear_documento_moderno.html',
            'taller/documentos/crear_documento.html',
            'taller/documentos/lista_documentos.html'
        ]
        
        for template in old_templates:
            found_in = []
            for py_file in python_files:
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        if template in f.read():
                            found_in.append(py_file)
                except (UnicodeDecodeError, PermissionError):
                    continue
            
            if found_in:
                self.log(f"⚠️  '{template}' aún referenciado en {len(found_in)} archivos", "WARNING")
                for file in found_in[:3]:  # Mostrar solo los primeros 3
                    rel_path = os.path.relpath(file, self.base_path)
                    self.log(f"    📁 {rel_path}")
                if len(found_in) > 3:
                    self.log(f"    ... y {len(found_in) - 3} más")
            else:
                self.log(f"✅ '{template}' - No encontrado en archivos Python")
    
    def run_verification(self):
        """Ejecutar verificación completa"""
        self.log("🚀 Iniciando verificación estática de migración de templates")
        self.log("="*70)
        
        self.check_settings_configuration()
        self.check_template_structure()
        self.check_views_use_mixin()
        self.check_urls_updated()
        self.check_old_template_references()
        
        self.log("="*70)
        self.log("📋 VERIFICACIÓN COMPLETADA")
        self.log("✅ Si todos los checks pasaron, la migración está lista para testing")

if __name__ == "__main__":
    print("🔧 Verificador Estático de Template Resolution - E-Garage")
    print("Este script verifica la configuración de archivos para la migración")
    print()
    
    verifier = StaticTemplateVerifier()
    verifier.run_verification()
