#!/usr/bin/env python
"""
Script para verificar la integración entre taller2 y la creación de documentos
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'e_garage.settings')

# Configurar temporalmente SQLite
import django
from django.conf import settings

# Sobrescribir configuración de base de datos
settings.DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

django.setup()

from django.contrib.auth.models import User
from taller.models.perfilusuario import PerfilUsuario
from taller.models.empresa import Empresa

def verificar_empresa_taller2():
    print("=== VERIFICACIÓN EMPRESA TALLER2 ===\n")
    
    try:
        # Obtener usuario taller2
        user = User.objects.get(username='taller2')
        print(f"✅ Usuario: {user.username}")
        
        # Verificar PerfilUsuario
        perfil = PerfilUsuario.objects.get(user=user)
        print(f"✅ PerfilUsuario encontrado - Empresa: {perfil.empresa.nombre_taller}")
        
        # Verificar la relación empresa_usuario (la que usa la vista)
        print("\n🔍 Verificando relación empresa_usuario:")
        try:
            empresa_usuario = user.empresa_usuario
            print(f"✅ user.empresa_usuario funciona: {empresa_usuario.nombre_taller}")
        except AttributeError as e:
            print(f"❌ ERROR: user.empresa_usuario no funciona: {e}")
            print("⚠️ Esto explicaría por qué los documentos no se guardan correctamente")
            
            # Verificar todas las empresas
            print("\n📋 Empresas en el sistema:")
            for emp in Empresa.objects.all():
                print(f"  - {emp.nombre_taller} (usuario: {emp.usuario})")
            
            # Verificar si hay una empresa sin usuario específico
            empresas_sin_usuario = Empresa.objects.filter(usuario__isnull=True)
            print(f"\n📋 Empresas sin usuario: {empresas_sin_usuario.count()}")
            
        # Verificar que la empresa esté bien asociada al usuario taller2
        print(f"\n🔍 Verificando empresa específica de taller2:")
        print(f"   PerfilUsuario.empresa: {perfil.empresa}")
        print(f"   PerfilUsuario.empresa.usuario: {perfil.empresa.usuario}")
        
        if perfil.empresa.usuario != user:
            print("❌ PROBLEMA: La empresa del PerfilUsuario no está asociada al usuario taller2")
            print("   Corrigiendo asociación...")
            perfil.empresa.usuario = user
            perfil.empresa.save()
            print("✅ Asociación corregida")
        else:
            print("✅ La empresa está correctamente asociada al usuario")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verificar_empresa_taller2()
