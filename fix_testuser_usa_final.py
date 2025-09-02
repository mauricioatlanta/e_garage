#!/usr/bin/env python
"""
Script definitivo para cambiar el país de testuser_usa
"""
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from django.contrib.auth.models import User
from taller.models import Empresa

try:
    user = User.objects.get(username='testuser_usa')
    print(f"Usuario: {user.username} (ID: {user.pk})")
    
    # Buscar todas las empresas relacionadas con este usuario
    empresas_user = Empresa.objects.filter(user=user)
    empresas_usuario = Empresa.objects.filter(usuario=user)
    
    print(f"Empresas con campo 'user': {empresas_user.count()}")
    for emp in empresas_user:
        print(f"  - {emp.nombre_taller} (País actual: {emp.pais})")
        emp.pais = 'US'
        emp.save()
        print(f"    → Cambiado a: US")
    
    print(f"Empresas con campo 'usuario': {empresas_usuario.count()}")
    for emp in empresas_usuario:
        print(f"  - {emp.nombre_taller} (País actual: {emp.pais})")
        emp.pais = 'US'
        emp.save()
        print(f"    → Cambiado a: US")
    
    # Si no hay empresas, crear una
    if not empresas_user.exists() and not empresas_usuario.exists():
        print("No hay empresas, creando una nueva...")
        empresa = Empresa.objects.create(
            user=user,
            nombre_taller="USA Test Garage",
            pais='US'
        )
        print(f"✅ Empresa creada: {empresa.nombre_taller} (País: {empresa.pais})")
    
    print("\n✅ Proceso completado!")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
