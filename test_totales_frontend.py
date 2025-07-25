#!/usr/bin/env python
"""
Script para probar que los totales se calculan correctamente en el frontend
"""

import os
import sys
import django

# Configurar el entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings_sqlite')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from taller.models.empresa import Empresa
from taller.models.perfilusuario import PerfilUsuario

print("=== PRUEBA DE TOTALES EN EL FRONTEND ===")

# Crear cliente de prueba
client = Client()

# Crear o obtener usuario de prueba
user, created = User.objects.get_or_create(
    username='test_totales',
    defaults={
        'email': 'test_totales@example.com',
        'first_name': 'Test',
        'last_name': 'Totales'
    }
)

if created:
    user.set_password('password123')
    user.save()
    print(f"✅ Usuario creado: {user.username}")
else:
    print(f"✅ Usuario existente: {user.username}")

# Crear o obtener empresa
empresa, created = Empresa.objects.get_or_create(
    usuario=user,
    defaults={
        'nombre_taller': 'Taller de Prueba Totales',
        'direccion': 'Dirección de prueba',
        'telefono': '123456789',
        'rut': '12345678-9'
    }
)

if created:
    print(f"✅ Empresa creada: {empresa.nombre_taller}")
else:
    print(f"✅ Empresa existente: {empresa.nombre_taller}")

# Crear o obtener perfil
perfil, created = PerfilUsuario.objects.get_or_create(
    user=user,
    defaults={
        'empresa': empresa,
        'rol': 'admin'
    }
)

if created:
    print(f"✅ Perfil creado para: {perfil.user.username}")
else:
    print(f"✅ Perfil existente para: {perfil.user.username}")

# Hacer login
client.force_login(user)
print(f"✅ Login exitoso para: {user.username}")

# Hacer una petición GET a la página de crear documento
try:
    response = client.get('/documentos/nuevo/')
    print(f"✅ Respuesta GET /documentos/nuevo/: {response.status_code}")
    
    if response.status_code == 200:
        content = response.content.decode('utf-8')
        
        # Verificar que los elementos necesarios están en el HTML
        elements_to_check = [
            'id="tabla-repuestos"',
            'id="tabla-servicios"',
            'id="total-repuestos"',
            'id="total-servicios"',
            'id="subtotal-doc"',
            'id="iva-doc"',
            'id="gran-total-doc"',
            'formulario_documento.js'
        ]
        
        print("\n=== VERIFICACIÓN DE ELEMENTOS EN EL HTML ===")
        for element in elements_to_check:
            if element in content:
                print(f"✅ {element} encontrado")
            else:
                print(f"❌ {element} NO encontrado")
        
        print("\n=== INSTRUCCIONES PARA PRUEBA MANUAL ===")
        print("1. Ve a http://127.0.0.1:8000/documentos/nuevo/")
        print("2. Llena los campos obligatorios del formulario")
        print("3. Haz clic en 'Agregar Repuesto' y agrega un repuesto con precio")
        print("4. Haz clic en 'Agregar Servicio' y agrega un servicio con precio")
        print("5. Verifica que los totales se actualicen automáticamente")
        print("6. Marca/desmarca el checkbox 'Incluir IVA' y verifica que el total cambie")
        
    else:
        print(f"❌ Error en la respuesta: {response.status_code}")
        
except Exception as e:
    print(f"❌ Error al hacer la petición: {e}")
    import traceback
    traceback.print_exc()

print("\n=== PRUEBA COMPLETADA ===")
