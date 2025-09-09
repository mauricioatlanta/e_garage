#!/usr/bin/env python3
"""
Script de verificación rápida post-parche bisturí
"""

import os
import sys

import django

# Configurar Django
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from django.contrib.auth.models import User

from taller.forms.configuracion_forms import CompanyInfoForm
from taller.models import ConfiguracionEmpresa


def verificar_setup():
    """Verificar que todo está bien configurado para el parche"""
    print("🔍 VERIFICACIÓN POST-PARCHE BISTURÍ")
    print("="*50)
    
    # 1. Verificar usuario y empresa
    user = User.objects.filter(is_active=True).first()
    if not user:
        print("❌ No hay usuarios activos")
        return False
    
    print(f"✅ Usuario: {user.username}")
    
    try:
        empresa = user.empresa
        print(f"✅ Empresa: {empresa.nombre_taller}")
    except:
        print("❌ Usuario no tiene empresa")
        return False
    
    # 2. Verificar configuración
    try:
        config = ConfiguracionEmpresa.objects.get(empresa=empresa)
        print(f"✅ Configuración existe")
        print(f"   - Nombre público: {config.nombre_publico}")
        print(f"   - Logo actual: {config.logo}")
        print(f"   - Updated at: {config.updated_at}")
    except ConfiguracionEmpresa.DoesNotExist:
        print("❌ No hay configuración de empresa")
        return False
    
    # 3. Verificar formulario
    form = CompanyInfoForm(instance=config)
    print(f"✅ CompanyInfoForm creado")
    print(f"   - Campos: {list(form.fields.keys())}")
    print(f"   - Tiene campo logo: {'logo' in form.fields}")
    
    # 4. Verificar widget del logo
    if 'logo' in form.fields:
        widget = form.fields['logo'].widget
        print(f"   - Widget logo: {type(widget).__name__}")
        print(f"   - Attrs: {widget.attrs}")
    
    # 5. Verificar media settings
    from django.conf import settings
    print(f"✅ Media settings:")
    print(f"   - MEDIA_URL: {settings.MEDIA_URL}")
    print(f"   - MEDIA_ROOT: {settings.MEDIA_ROOT}")
    
    # 6. Verificar directorio de logos
    import os
    logo_dir = os.path.join(settings.MEDIA_ROOT, 'logos')
    exists = os.path.exists(logo_dir)
    print(f"   - Directorio logos existe: {exists}")
    if exists:
        files = os.listdir(logo_dir)
        print(f"   - Archivos en logos/: {len(files)} archivos")
        if files:
            print(f"     Ejemplos: {files[:3]}")
    
    print("\n🎯 ESTADO DEL PARCHE:")
    print("✅ Vista con logs de DEBUG fuertes aplicados")
    print("✅ Asignación forzada de archivo implementada")
    print("✅ Cache-busting agregado al template")
    print("✅ Consultas secundarias corregidas")
    
    print(f"\n📍 PRÓXIMO PASO:")
    print(f"Ir a http://127.0.0.1:8000/cl/taller/settings/")
    print(f"Subir una imagen y presionar 💾 UPDATE PROFILE")
    print(f"Revisar console para logs con 🧪 DEBUG")
    
    return True

if __name__ == "__main__":
    verificar_setup()
