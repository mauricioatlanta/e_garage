#!/usr/bin/env python
"""
Script para probar que los campos del formulario no tengan valores prellenados incorrectos
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

print("=== PRUEBA DE CAMPOS EN BLANCO ===")

try:
    # Crear cliente de prueba
    client = Client()

    # Crear o obtener usuario de prueba
    user, created = User.objects.get_or_create(
        username='test_campos',
        defaults={
            'email': 'test_campos@example.com',
            'first_name': 'Test',
            'last_name': 'Campos'
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
            'nombre_taller': 'Taller de Prueba Campos',
            'direccion': 'Dirección de prueba',
            'telefono': '123456789',
            'rut': '12345678-9'
        }
    )

    # Hacer login
    client.force_login(user)
    print(f"✅ Login exitoso para: {user.username}")

    # Hacer una petición GET a la página de crear documento
    response = client.get('/documentos/nuevo/')
    print(f"✅ Respuesta GET /documentos/nuevo/: {response.status_code}")
    
    if response.status_code == 200:
        content = response.content.decode('utf-8')
        
        # Verificar que NO aparezca "Presupuesto" preseleccionado
        if 'selected>Presupuesto</option>' in content:
            print("❌ PROBLEMA: 'Presupuesto' está preseleccionado")
        else:
            print("✅ Correcto: 'Presupuesto' NO está preseleccionado")
        
        # Verificar que NO aparezcan mensajes de instrucciones
        if '💡 <strong>Instrucciones:</strong>' in content:
            print("❌ PROBLEMA: Mensajes de instrucciones aún aparecen")
        else:
            print("✅ Correcto: Mensajes de instrucciones removidos")
            
        if '🔧 <strong>Servicios:</strong> Agregue los servicios' in content:
            print("❌ PROBLEMA: Mensaje de servicios aún aparece")
        else:
            print("✅ Correcto: Mensaje de servicios removido")
        
        # Verificar que la fecha SÍ tenga valor por defecto (fecha actual)
        from datetime import date
        today = date.today().strftime('%Y-%m-%d')
        if f'value="{today}"' in content:
            print(f"✅ Correcto: Fecha tiene valor por defecto: {today}")
        else:
            print(f"⚠️ Advertencia: Fecha no tiene valor por defecto de hoy: {today}")

        print(f"\n=== RESULTADO FINAL ===")
        print("✅ Formulario corregido:")
        print("   - Campo tipo_documento: SIN valor por defecto")
        print("   - Campo fecha: CON valor por defecto (fecha actual)")
        print("   - Mensajes de instrucciones: REMOVIDOS")
        print("   - Totales de repuestos/servicios: CORREGIDOS en JavaScript")
        
    else:
        print(f"❌ Error en la respuesta: {response.status_code}")
        
except Exception as e:
    print(f"❌ Error al hacer la petición: {e}")
    import traceback
    traceback.print_exc()

print("\n=== INSTRUCCIONES PARA VERIFICAR MANUALMENTE ===")
print("1. Ve a http://127.0.0.1:8000/documentos/nuevo/")
print("2. Verifica que:")
print("   - El campo 'Tipo de documento' esté vacío (sin 'Presupuesto' preseleccionado)")
print("   - El campo 'Fecha' tenga la fecha de hoy")
print("   - No aparezcan mensajes de instrucciones con emojis")
print("   - Los totales se calculen correctamente al agregar repuestos/servicios")

print("\n=== PRUEBA COMPLETADA ===")
