#!/usr/bin/env python3
"""
Script para verificar usuarios y credenciales de prueba
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from taller.models.empresa import Empresa
from taller.models.suscripcion import Suscripcion

print('=' * 80)
print('🔐 USUARIOS Y CREDENCIALES DE PRUEBA - E-GARAGE')
print('=' * 80)
print()

print('📋 CREDENCIALES PRINCIPALES:')
print('-' * 50)

usuarios_prueba = [
    ('admin', 'admin123', '👑 Administrador del sistema'),
    ('taller1', 'taller123', '🔧 Taller AutoFix'),
    ('taller2', 'taller123', '🔧 Taller Premium')
]

for username, password, descripcion in usuarios_prueba:
    user = authenticate(username=username, password=password)
    estado = '✅ VÁLIDO' if user else '❌ INVÁLIDO'
    print(f'{username:<12} | {password:<12} | {estado} | {descripcion}')

print()
print('🗂️ TODOS LOS USUARIOS EN BASE DE DATOS:')
print('-' * 70)

for user in User.objects.all():
    # Buscar empresa asociada
    try:
        empresa = Empresa.objects.get(usuario=user)
        empresa_info = f"({empresa.nombre_taller})"
    except Empresa.DoesNotExist:
        empresa_info = "(Sin empresa)"
    
    # Buscar suscripción
    try:
        suscripcion = user.suscripcion
        suscripcion_info = f"{suscripcion.plan} - {'Activa' if suscripcion.activa else 'Inactiva'}"
    except:
        suscripcion_info = "Sin suscripción"
    
    estado_user = "👑 Admin" if user.is_superuser else ("👤 Staff" if user.is_staff else "👥 Usuario")
    
    print(f'{user.username:<15} | {user.email:<25} | {estado_user} | {empresa_info}')
    if hasattr(user, 'suscripcion'):
        print(f'{"" : <15} | {"" : <25} | 📅 {suscripcion_info}')

print()
print('🎯 ACCESO RÁPIDO:')
print('-' * 30)
print('🌐 URL: http://127.0.0.1:8000/')
print('📊 Admin: http://127.0.0.1:8000/admin/')
print('📈 Reportes: http://127.0.0.1:8000/reportes/')
print()
print('🔑 CREDENCIALES DE ACCESO:')
print('   👑 Admin: admin / admin123')
print('   🔧 Taller 1: taller1 / taller123')
print('   🔧 Taller 2: taller2 / taller123')
print()
print('=' * 80)
