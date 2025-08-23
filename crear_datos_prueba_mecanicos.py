#!/usr/bin/env python3
"""
Script para crear datos de prueba para el sistema de mecánicos
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'e_garage.settings')
django.setup()

from django.contrib.auth.models import User
from taller.models.empresa import Empresa
from taller.models.tecnico import Mecanico
from taller.models.perfilusuario import PerfilUsuario

def crear_datos_prueba():
    print("🔧 Creando datos de prueba para mecánicos...")
    
    # Crear usuario de prueba si no existe
    user, created = User.objects.get_or_create(
        username='admin_taller',
        defaults={
            'email': 'admin@taller.com',
            'first_name': 'Admin',
            'last_name': 'Taller',
            'is_staff': True,
            'is_superuser': True
        }
    )
    
    if created:
        user.set_password('admin123')
        user.save()
        print(f"✅ Usuario creado: {user.username}")
    else:
        print(f"ℹ️ Usuario ya existe: {user.username}")
    
    # Crear empresa de prueba
    empresa, created = Empresa.objects.get_or_create(
        usuario=user,
        defaults={
            'nombre_taller': 'Taller de Prueba',
            'direccion': 'Calle Falsa 123',
            'telefono': '+1234567890',
            'email': 'taller@prueba.com'
        }
    )
    
    if created:
        print(f"✅ Empresa creada: {empresa.nombre_taller}")
    else:
        print(f"ℹ️ Empresa ya existe: {empresa.nombre_taller}")
    
    # Crear perfil de usuario
    perfil, created = PerfilUsuario.objects.get_or_create(
        user=user,
        defaults={
            'empresa': empresa,
            'es_superadmin': False
        }
    )
    
    if created:
        print(f"✅ Perfil creado para: {user.username}")
    else:
        print(f"ℹ️ Perfil ya existe para: {user.username}")
    
    # Crear mecánicos de prueba
    mecanicos_datos = [
        {'nombre': 'Juan Carlos', 'activo': True},
        {'nombre': 'María González', 'activo': True},
        {'nombre': 'Pedro Martínez', 'activo': True},
        {'nombre': 'Ana López', 'activo': False},  # Inactivo para probar filtrado
        {'nombre': 'Luis Rodriguez', 'activo': True},
    ]
    
    for mec_data in mecanicos_datos:
        mecanico, created = Tecnico.objects.get_or_create(
            empresa=empresa,
            nombre=mec_data['nombre'],
            defaults={'activo': mec_data['activo']}
        )
        
        if created:
            status = "✅ ACTIVO" if mecanico.activo else "❌ INACTIVO"
            print(f"{status} Mecánico creado: {mecanico.nombre}")
        else:
            status = "✅ ACTIVO" if mecanico.activo else "❌ INACTIVO"
            print(f"{status} Mecánico ya existe: {mecanico.nombre}")
    
    print("\n🎉 Datos de prueba creados exitosamente!")
    print("\n📝 Para probar:")
    print(f"1. Ve a http://127.0.0.1:8000/admin/ (usuario: {user.username}, password: admin123)")
    print("2. Ve a http://127.0.0.1:8000/documentos/ para ver documentos")
    print("3. Ve a http://127.0.0.1:8000/documentos/nuevo/ para crear un documento")
    print("\n🔍 Deberías ver solo los mecánicos activos en el formulario de creación de documentos")

if __name__ == '__main__':
    crear_datos_prueba()
