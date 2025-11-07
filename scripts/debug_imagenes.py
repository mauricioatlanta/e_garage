#!/usr/bin/env python
"""
Script para diagnosticar el problema de subida de imágenes en configuración
"""
import os
import sys

import django

# Agregar el directorio del proyecto al path
sys.path.append(os.path.join(os.path.dirname(__file__)))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'e_garage.settings')
django.setup()

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile

from taller.forms.empresa import EmpresaForm
from taller.models.empresa import Empresa


def diagnosticar_subida_imagenes():
    """Diagnostica problemas con la subida de imágenes"""
    print("🔍 DIAGNÓSTICO DE SUBIDA DE IMÁGENES")
    print("=" * 50)
    
    # 1. Verificar configuración de medios
    print("\n1. CONFIGURACIÓN DE MEDIOS:")
    print(f"   MEDIA_URL: {settings.MEDIA_URL}")
    print(f"   MEDIA_ROOT: {settings.MEDIA_ROOT}")
    print(f"   Directorio existe: {os.path.exists(settings.MEDIA_ROOT)}")
    
    # 2. Verificar directorio de logos
    logos_dir = os.path.join(settings.MEDIA_ROOT, 'logos_talleres')
    print(f"\n2. DIRECTORIO DE LOGOS:")
    print(f"   Path: {logos_dir}")
    print(f"   Existe: {os.path.exists(logos_dir)}")
    
    # Crear directorio si no existe
    if not os.path.exists(logos_dir):
        try:
            os.makedirs(logos_dir, exist_ok=True)
            print(f"   ✅ Directorio creado: {logos_dir}")
        except Exception as e:
            print(f"   ❌ Error creando directorio: {e}")
    
    # 3. Buscar usuario de prueba
    print(f"\n3. USUARIOS DE PRUEBA:")
    usuarios = User.objects.all()[:3]
    for user in usuarios:
        print(f"   Usuario: {user.username} (ID: {user.id})")
        try:
            empresa = user.empresa
            print(f"     Empresa: {empresa.nombre_taller}")
            if empresa.logo:
                print(f"     Logo: {empresa.logo.url}")
            else:
                print(f"     Logo: Sin logo")
        except:
            print(f"     Empresa: No tiene empresa")
    
    # 4. Probar formulario
    print(f"\n4. PRUEBA DE FORMULARIO:")
    if usuarios.exists():
        user = usuarios.first()
        try:
            empresa, created = Empresa.objects.get_or_create(usuario=user)
            print(f"   Empresa de prueba: {empresa.nombre_taller}")
            
            # Crear archivo de prueba
            test_image_content = b"fake image content"
            test_file = SimpleUploadedFile("test_logo.png", test_image_content, content_type="image/png")
            
            # Crear formulario con imagen
            form_data = {
                'nombre_taller': 'Taller de Prueba',
                'empresa': 'Empresa Test',
                'direccion': 'Dirección Test',
                'telefono': '+56912345678'
            }
            form_files = {'logo': test_file}
            
            form = EmpresaForm(data=form_data, files=form_files, instance=empresa)
            print(f"   Formulario válido: {form.is_valid()}")
            
            if not form.is_valid():
                print(f"   Errores: {form.errors}")
            else:
                print(f"   ✅ Formulario se puede procesar")
                
        except Exception as e:
            print(f"   ❌ Error en prueba: {e}")
    
    print("\n" + "=" * 50)
    print("DIAGNÓSTICO COMPLETADO")

if __name__ == "__main__":
    diagnosticar_subida_imagenes()
