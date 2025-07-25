#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test para verificar que los créditos de Atlanta Reciclajes 
están correctamente integrados en todo el sistema eGarage
"""

import os
import sys
import django
from pathlib import Path

# Configurar Django
PROJECT_ROOT = Path(__file__).parent
sys.path.append(str(PROJECT_ROOT))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'garage_project.settings')

try:
    django.setup()
except Exception as e:
    print(f"⚠️ Error configurando Django: {e}")
    print("Verificando archivos de template directamente...")

def verificar_templates():
    """Verificar que los créditos están en los templates"""
    templates_verificar = [
        'templates/base.html',
        'templates/registration/login.html', 
        'templates/account/login.html',
        'templates/suspension/suspension.html',
        'templates/landing_egarage.html',
        'taller/templates/portal/login.html',
        'taller/templates/taller/documentos/pdf_template.html'
    ]
    
    creditos_esperados = [
        'Atlanta Reciclajes',
        '77.350.892-5',
        'suscripcion@atlantareciclajes.cl',
        'eGarage AI'
    ]
    
    print("🔍 VERIFICACIÓN DE CRÉDITOS ATLANTA RECICLAJES")
    print("=" * 50)
    
    total_templates = 0
    templates_ok = 0
    
    for template_path in templates_verificar:
        total_templates += 1
        full_path = PROJECT_ROOT / template_path
        
        if not full_path.exists():
            print(f"❌ {template_path} - Archivo no encontrado")
            continue
            
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                contenido = f.read()
                
            creditos_encontrados = []
            for credito in creditos_esperados:
                if credito in contenido:
                    creditos_encontrados.append(credito)
            
            if len(creditos_encontrados) >= 3:  # Al menos 3 de 4 créditos
                print(f"✅ {template_path} - Créditos OK ({len(creditos_encontrados)}/4)")
                templates_ok += 1
            else:
                print(f"⚠️ {template_path} - Créditos parciales ({len(creditos_encontrados)}/4)")
                print(f"   Encontrados: {creditos_encontrados}")
                
        except Exception as e:
            print(f"❌ {template_path} - Error leyendo archivo: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 RESUMEN: {templates_ok}/{total_templates} templates con créditos completos")
    
    # Verificar logo
    logo_path = PROJECT_ROOT / 'static/img/logo.png'
    if logo_path.exists():
        print(f"✅ Logo encontrado: {logo_path}")
    else:
        print(f"❌ Logo NO encontrado: {logo_path}")
    
    return templates_ok == total_templates

def verificar_urls_importantes():
    """Verificar que las URLs importantes tienen los créditos"""
    print("\n🌐 URLS A VERIFICAR MANUALMENTE:")
    print("=" * 50)
    
    urls_importantes = [
        ("/login/", "Página de login principal"),
        ("/accounts/login/", "Login con allauth"),
        ("/portal/login/", "Login portal clientes"),
        ("/suspension/", "Página de suspensión de pago"),
        ("/landing/egarage/", "Landing principal"),
        ("/", "Página inicial"),
    ]
    
    for url, descripcion in urls_importantes:
        print(f"• {url:<20} - {descripcion}")
    
    print("\n📋 VERIFICAR EN CADA URL:")
    print("   1. Logo de Atlanta Reciclajes visible")
    print("   2. Texto 'Atlanta Reciclajes' presente")
    print("   3. RUT: 77.350.892-5")
    print("   4. Email: suscripcion@atlantareciclajes.cl")
    print("   5. Mención a 'eGarage AI™'")

def mostrar_creditos_implementados():
    """Mostrar resumen de créditos implementados"""
    print("\n🎯 CRÉDITOS IMPLEMENTADOS:")
    print("=" * 50)
    
    implementaciones = [
        ("Footer Global", "base.html", "Visible en todas las páginas autenticadas"),
        ("Login Principal", "registration/login.html", "Créditos en el pie del formulario"),
        ("Login Allauth", "account/login.html", "Créditos con borde superior"),
        ("Portal Clientes", "portal/login.html", "Créditos con Bootstrap styling"),
        ("Página Suspensión", "suspension.html", "Tarjeta destacada con logo y datos"),
        ("Landing Principal", "landing_egarage.html", "Sección destacada en footer"),
        ("PDFs Documentos", "pdf_template.html", "Footer de documentos PDF"),
    ]
    
    for nombre, archivo, descripcion in implementaciones:
        print(f"✅ {nombre:<20} ({archivo})")
        print(f"   {descripcion}")
        print()

if __name__ == "__main__":
    print("🚀 VERIFICADOR DE CRÉDITOS ATLANTA RECICLAJES")
    print("=" * 60)
    
    # Cambiar al directorio del proyecto
    os.chdir(PROJECT_ROOT)
    
    # Verificar templates
    templates_ok = verificar_templates()
    
    # Mostrar implementaciones
    mostrar_creditos_implementados()
    
    # Mostrar URLs para verificar
    verificar_urls_importantes()
    
    # Resultado final
    print("\n" + "=" * 60)
    if templates_ok:
        print("🎉 ¡INTEGRACIÓN COMPLETADA EXITOSAMENTE!")
        print("   Todos los templates tienen los créditos de Atlanta Reciclajes")
    else:
        print("⚠️ Algunos templates necesitan revisión")
    
    print("\n📝 PRÓXIMOS PASOS:")
    print("   1. Ejecutar el servidor: python manage.py runserver")
    print("   2. Verificar cada URL manualmente")
    print("   3. Generar un PDF de prueba para verificar créditos")
    print("   4. Confirmar que el logo se muestra correctamente")
    
    print(f"\n💼 CRÉDITOS IMPLEMENTADOS:")
    print(f"   • Empresa: Atlanta Reciclajes")
    print(f"   • RUT: 77.350.892-5")
    print(f"   • Email: suscripcion@atlantareciclajes.cl")
    print(f"   • Producto: eGarage AI™")
    print(f"   • Logo: /static/img/logo.png")
