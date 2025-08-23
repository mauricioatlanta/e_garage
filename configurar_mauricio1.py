#!/usr/bin/env python
import os
import django
from django.core.files.base import ContentFile
import requests

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from django.contrib.auth.models import User
from taller.models.empresa import Empresa

print("🔧 CONFIGURANDO USUARIO MAURICIO1 PARA PRUEBAS")
print("=" * 50)

try:
    # Buscar usuario mauricio1
    user = User.objects.get(username='mauricio1')
    empresa = user.empresa
    
    print(f"✅ Usuario encontrado: {user.username}")
    print(f"✅ Empresa: {empresa.nombre_taller}")
    print(f"✅ País: {empresa.get_pais_display()}")
    
    # Cambiar nombre de empresa para que sea más personalizado
    empresa.nombre_taller = "Taller Mecánico El Turbo"
    empresa.empresa = "Turbo Automotive Services SpA"
    empresa.direccion = "Av. Providencia 1234, Santiago, Chile"
    empresa.telefono = "+56 9 8765 4321"
    empresa.email = "gerencia@elturbo.cl"
    
    # Descargar un logo de ejemplo (puedes cambiar esta URL)
    logo_url = "https://via.placeholder.com/200x100/003d82/ffffff?text=TURBO+AUTO"
    
    try:
        response = requests.get(logo_url)
        if response.status_code == 200:
            # Guardar el logo
            logo_file = ContentFile(response.content, name='logo_turbo.png')
            empresa.logo.save('logo_turbo.png', logo_file, save=False)
            print("✅ Logo personalizado agregado")
        else:
            print("⚠️ No se pudo descargar el logo, usando configuración sin logo")
    except Exception as e:
        print(f"⚠️ Error descargando logo: {e}")
    
    empresa.save()
    
    print()
    print("🎉 EMPRESA CONFIGURADA:")
    print(f"- Nombre: {empresa.nombre_taller}")
    print(f"- Empresa: {empresa.empresa}")
    print(f"- Dirección: {empresa.direccion}")
    print(f"- Teléfono: {empresa.telefono}")
    print(f"- Email: {empresa.email}")
    print(f"- Logo: {'✅ Configurado' if empresa.logo else '❌ Sin logo'}")
    print()
    print("🔐 CREDENCIALES DE ACCESO:")
    print(f"- Usuario: mauricio1")
    print(f"- Password: taller123")
    print(f"- URL: http://127.0.0.1:8000/cl/")
    
except User.DoesNotExist:
    print("❌ Usuario mauricio1 no encontrado")
except Exception as e:
    print(f"❌ Error: {e}")
