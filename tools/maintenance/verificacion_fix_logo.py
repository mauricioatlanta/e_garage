#!/usr/bin/env python3
"""
🔧 SCRIPT DE VERIFICACIÓN FINAL PARA FIX DE LOGO
Verifica que el fix garantizado esté funcionando correctamente
"""

import os
import sys
from io import BytesIO

from PIL import Image

import django

# Configurar Django
project_root = "e:/projecto/e_garage"
sys.path.insert(0, project_root)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile

from taller.forms.configuracion_forms import CompanyInfoForm
from taller.models import ConfiguracionEmpresa

print("🧪 === VERIFICACIÓN DEL FIX GARANTIZADO ===")
print()

# 1. Verificar que CompanyInfoForm existe y funciona
print("1️⃣ Verificando CompanyInfoForm...")
try:
    form = CompanyInfoForm()
    print("✅ CompanyInfoForm importado correctamente")
    print(f"   Campos disponibles: {list(form.fields.keys())}")
    if "logo" in form.fields:
        print("✅ Campo 'logo' presente en el formulario")
    else:
        print("❌ Campo 'logo' NO presente en el formulario")
except Exception as e:
    print(f"❌ Error importando CompanyInfoForm: {e}")

print()

# 2. Verificar usuario y configuración
print("2️⃣ Verificando usuario de Chile...")
try:
    # Buscar usuario activo
    user = User.objects.filter(is_active=True).first()
    if user:
        print(f"✅ Usuario encontrado: {user.username}")
        if hasattr(user, "empresa"):
            print(f"   Empresa: {user.empresa.nombre_taller}")
            print(f"   País: {getattr(user.empresa, 'pais', 'N/A')}")
        else:
            print("❌ Usuario no tiene empresa asociada")
    else:
        print("❌ No hay usuarios activos")
except Exception as e:
    print(f"❌ Error buscando usuario: {e}")

print()

# 3. Verificar configuración de empresa
print("3️⃣ Verificando ConfiguracionEmpresa...")
try:
    if user and hasattr(user, "empresa"):
        config = ConfiguracionEmpresa.objects.get(empresa=user.empresa)
        print("✅ ConfiguracionEmpresa encontrada")
        print(f"   Nombre público: {config.nombre_publico}")
        print(f"   Logo actual: {config.logo}")
        print(f"   Logo URL: {config.logo.url if config.logo else 'Sin logo'}")
    else:
        print("❌ No se puede verificar ConfiguracionEmpresa sin usuario/empresa")
except ConfiguracionEmpresa.DoesNotExist:
    print("❌ ConfiguracionEmpresa no existe para esta empresa")
except Exception as e:
    print(f"❌ Error: {e}")

print()

# 4. Test completo del formulario con logo
print("4️⃣ Test completo del formulario con logo...")
try:
    if user and hasattr(user, "empresa"):
        # Crear imagen de prueba
        img = Image.new("RGB", (100, 100), color="blue")
        img_io = BytesIO()
        img.save(img_io, format="PNG")
        img_io.seek(0)

        # Crear archivo uploaded
        uploaded_file = SimpleUploadedFile(
            "test_fix.png", img_io.getvalue(), content_type="image/png"
        )

        # Obtener configuración
        config = ConfiguracionEmpresa.objects.get(empresa=user.empresa)
        logo_antes = str(config.logo) if config.logo else "Sin logo"

        # Test del formulario
        form_data = {
            "nombre_publico": "Test Fix Garantizado",
            "tagline": "Logo funcionando",
            "iva_porcentaje": 19,
        }
        file_data = {"logo": uploaded_file}

        form = CompanyInfoForm(form_data, file_data, instance=config)

        if form.is_valid():
            print("✅ Formulario válido")
            obj = form.save()
            print("✅ Guardado exitoso")
            print(f"   Logo antes: {logo_antes}")
            print(f"   Logo después: {obj.logo}")
            print(f"   URL después: {obj.logo.url if obj.logo else 'Sin URL'}")
        else:
            print("❌ Formulario no válido:")
            for field, errors in form.errors.items():
                print(f"   {field}: {errors}")
    else:
        print("❌ No se puede hacer test sin usuario/empresa válidos")

except Exception as e:
    print(f"❌ Error en test: {e}")

print()

# 5. Verificar configuración MEDIA
print("5️⃣ Verificando configuración MEDIA...")
try:
    from django.conf import settings

    print(f"✅ MEDIA_URL: {settings.MEDIA_URL}")
    print(f"✅ MEDIA_ROOT: {settings.MEDIA_ROOT}")

    # Verificar que el directorio media existe
    media_root = str(settings.MEDIA_ROOT)
    if os.path.exists(media_root):
        print(f"✅ Directorio MEDIA_ROOT existe: {media_root}")

        # Verificar directorio logos
        logos_dir = os.path.join(media_root, "logos")
        if os.path.exists(logos_dir):
            logo_files = os.listdir(logos_dir)
            print(f"✅ Directorio logos/ existe con {len(logo_files)} archivos")
            if logo_files:
                print(
                    f"   Archivos: {logo_files[:5]}{'...' if len(logo_files) > 5 else ''}"
                )
        else:
            print("⚠️  Directorio logos/ no existe")
    else:
        print(f"❌ Directorio MEDIA_ROOT no existe: {media_root}")

except Exception as e:
    print(f"❌ Error verificando MEDIA: {e}")

print()
print("🧪 === FIN DE VERIFICACIÓN ===")
print()
print("📋 RESUMEN:")
print("- Si todo muestra ✅, el fix está funcionando")
print("- Si hay ❌, revisar los errores mostrados arriba")
print("- Ahora prueba subir un logo en: http://127.0.0.1:8000/cl/taller/settings/")
print("- Usa el botón '💾 UPDATE PROFILE' del primer formulario")
