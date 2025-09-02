#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from django.contrib.auth.models import User
from taller.models import Empresa

print("=== ASIGNAR EMPRESA AL ADMIN ===")

try:
    admin = User.objects.get(username='admin')
    empresa = Empresa.objects.get(pk=1)  # USA Test Garage
    
    print(f"Usuario: {admin.username}")
    print(f"Empresa a asignar: {empresa.nombre_taller} (ID: {empresa.pk})")
    
    # Verificar si la empresa ya tiene un usuario
    if empresa.user:
        print(f"⚠️ La empresa ya está asignada a: {empresa.user.username}")
        print("Reasignando...")
    
    # Asignar
    empresa.user = admin
    empresa.save()
    
    print(f"✅ Admin asignado correctamente a: {empresa.nombre_taller}")
    
    # Verificar
    admin.refresh_from_db()
    if hasattr(admin, 'empresa') and admin.empresa:
        print(f"✅ Verificación: {admin.username} -> {admin.empresa.nombre_taller}")
    else:
        print("❌ La asignación no funcionó")
        
except Exception as e:
    print(f"❌ Error: {e}")
