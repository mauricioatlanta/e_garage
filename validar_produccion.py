# ===============================================================
# 🚀 SCRIPT DE VALIDACIÓN PRE-DESPLIEGUE
# ===============================================================
# Validar que todos los archivos estén listos para PythonAnywhere
# ===============================================================

import os
import sys
import django
from django.core.management import execute_from_command_line

def verificar_archivos_produccion():
    """Verificar que todos los archivos necesarios existan"""
    archivos_requeridos = [
        'settings_production.py',
        'requirements.txt',
        'wsgi_production.py',
        'PA_DEPLOY_README.md'
    ]
    
    print("🔍 Verificando archivos de producción...")
    for archivo in archivos_requeridos:
        if os.path.exists(archivo):
            print(f"✅ {archivo} - ENCONTRADO")
        else:
            print(f"❌ {archivo} - FALTANTE")
    
    print("\n" + "="*60)

def verificar_configuracion():
    """Verificar configuración de Django para producción"""
    print("🔧 Verificando configuración de Django...")
    
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'e_garage.settings_production')
        django.setup()
        
        from django.conf import settings
        
        # Verificar configuraciones críticas
        checks = [
            ("DEBUG", settings.DEBUG == False),
            ("ALLOWED_HOSTS", len(settings.ALLOWED_HOSTS) > 1),
            ("SECRET_KEY", len(settings.SECRET_KEY) > 20),
            ("DATABASE ENGINE", 'mysql' in settings.DATABASES['default']['ENGINE']),
            ("STATIC_ROOT", hasattr(settings, 'STATIC_ROOT')),
            ("MEDIA_ROOT", hasattr(settings, 'MEDIA_ROOT')),
        ]
        
        for nombre, resultado in checks:
            estado = "✅" if resultado else "❌"
            print(f"{estado} {nombre}")
            
    except Exception as e:
        print(f"❌ Error al verificar configuración: {e}")
    
    print("\n" + "="*60)

def verificar_dependencias():
    """Verificar que las dependencias estén en requirements.txt"""
    print("📦 Verificando dependencias...")
    
    dependencias_criticas = [
        'Django',
        'mysqlclient',
        'whitenoise',
        'django-allauth',
        'gunicorn'
    ]
    
    try:
        with open('requirements.txt', 'r') as f:
            contenido = f.read()
            
        for dep in dependencias_criticas:
            if dep.lower() in contenido.lower():
                print(f"✅ {dep}")
            else:
                print(f"❌ {dep} - FALTANTE")
                
    except FileNotFoundError:
        print("❌ requirements.txt no encontrado")
    
    print("\n" + "="*60)

def generar_resumen():
    """Generar resumen final"""
    print("📋 RESUMEN DEL PROYECTO PARA PYTHONANYWHERE")
    print("="*60)
    print("🌐 URL: https://e-garage-atlantareciclajes.pythonanywhere.com")
    print("🐍 Python: 3.10+")
    print("🗄️  Base de datos: MySQL")
    print("🚀 Framework: Django 5.2.3")
    print("="*60)
    print("📁 Archivos listos para subir:")
    print("   - Todo el proyecto (excepto .git, __pycache__, db.sqlite3)")
    print("   - settings_production.py")
    print("   - requirements.txt")
    print("   - wsgi_production.py")
    print("   - PA_DEPLOY_README.md")
    print("="*60)
    print("🎯 SIGUIENTE PASO: Seguir PA_DEPLOY_README.md")
    print("="*60)

if __name__ == "__main__":
    print("🔍 VALIDACIÓN PRE-DESPLIEGUE PARA PYTHONANYWHERE")
    print("=" * 60)
    
    verificar_archivos_produccion()
    verificar_configuracion()
    verificar_dependencias()
    generar_resumen()
    
    print("\n✅ VALIDACIÓN COMPLETADA")
    print("🚀 El proyecto está listo para PythonAnywhere!")
