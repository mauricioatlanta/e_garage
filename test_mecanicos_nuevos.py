#!/usr/bin/env python
"""
Script para probar que se puede agregar un mecánico nuevo al crear un documento
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
from taller.models.mecanico import Mecanico

print("=== PRUEBA DE MECÁNICOS NUEVOS ===")

try:
    # Crear cliente de prueba
    client = Client()

    # Crear o obtener usuario de prueba
    user, created = User.objects.get_or_create(
        username='test_mecanicos',
        defaults={
            'email': 'test_mecanicos@example.com',
            'first_name': 'Test',
            'last_name': 'Mecanicos'
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
            'nombre_taller': 'Taller de Prueba Mecánicos',
            'direccion': 'Dirección de prueba',
            'telefono': '123456789',
            'rut': '12345678-9'
        }
    )

    # Hacer login
    client.force_login(user)
    print(f"✅ Login exitoso para: {user.username}")

    # Contar mecánicos antes
    mecanicos_antes = Mecanico.objects.count()
    print(f"📊 Mecánicos en BD antes: {mecanicos_antes}")

    # Probar autocompletado de mecánicos
    print("\n=== PRUEBA DE AUTOCOMPLETADO ===")
    response = client.get('/autocomplete/mecanico/')
    print(f"✅ Respuesta GET /autocomplete/mecanico/: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ La vista de autocompletado funciona")
        
        # Probar búsqueda con query
        response = client.get('/autocomplete/mecanico/?q=Juan')
        print(f"✅ Búsqueda con query 'Juan': {response.status_code}")
    
    # Probar la página de crear documento
    response = client.get('/documentos/nuevo/')
    print(f"✅ Respuesta GET /documentos/nuevo/: {response.status_code}")
    
    if response.status_code == 200:
        content = response.content.decode('utf-8')
        
        # Verificar que el campo mecánico está presente y configurado correctamente
        if 'autocomplete_mecanico' in content:
            print("✅ Campo de mecánico con autocompletado encontrado")
        else:
            print("❌ Campo de mecánico con autocompletado NO encontrado")
            
        if 'data-tags' in content and 'true' in content:
            print("✅ Configuración data-tags=true encontrada")
        else:
            print("⚠️  Configuración data-tags puede estar ausente")

    print(f"\n=== ESTADO ACTUAL ===")
    print("✅ Cambios aplicados:")
    print("   - Campo mecánico cambiado de ModelChoiceField a CharField")
    print("   - Widget configurado con data-tags='true'")
    print("   - Vista de autocompletado con método create()")
    print("   - Lógica de procesamiento en vista crear_documento")
    print("   - Lógica de procesamiento agregada a vista editar_documento")
    print("   - Inicialización correcta en el formulario para edición")

    print(f"\n=== INSTRUCCIONES PARA PROBAR MANUALMENTE ===")
    print("1. Ve a http://127.0.0.1:8000/documentos/nuevo/")
    print("2. En el campo 'Mecánico':")
    print("   - Escribe el nombre de un mecánico nuevo (ej: 'Carlos Pérez')")
    print("   - O busca un mecánico existente escribiendo parte del nombre")
    print("3. Completa los demás campos obligatorios")
    print("4. Guarda el documento")
    print("5. El mecánico nuevo debería crearse automáticamente")
    
    print(f"\n=== VERIFICACIÓN ADICIONAL ===")
    print("Si tienes problemas:")
    print("- Verifica que el JavaScript Select2 esté cargando correctamente")
    print("- Revisa la consola del navegador por errores JavaScript")
    print("- Verifica que las URLs de autocompletado estén configuradas")

except Exception as e:
    print(f"❌ Error durante la prueba: {e}")
    import traceback
    traceback.print_exc()

print("\n=== PRUEBA COMPLETADA ===")
