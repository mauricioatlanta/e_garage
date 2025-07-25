import os
import django
import sys
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings_sqlite')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from taller.models.mecanico import Mecanico
import json

def test_crear_mecanico_api():
    """Test del endpoint de creación de mecánicos"""
    
    # Crear cliente de prueba
    client = Client()
    
    # Crear usuario para la sesión
    user = User.objects.first()
    if user:
        client.force_login(user)
    
    print("🧪 TESTING: API Crear Mecánico")
    
    # Test 1: Crear mecánico nuevo
    response = client.post('/documentos/api/crear_mecanico/', {
        'nombre': 'Carlos Mecánico Test'
    })
    
    print(f"📤 POST /api/crear_mecanico/ con nombre: 'Carlos Mecánico Test'")
    print(f"📊 Status: {response.status_code}")
    print(f"📄 Response: {response.content.decode()}")
    
    if response.status_code == 200:
        data = json.loads(response.content)
        print(f"✅ Mecánico creado: ID {data['id']}, Nombre: {data['nombre']}")
        
        # Verificar que existe en base de datos
        mecanico = Mecanico.objects.filter(id=data['id']).first()
        if mecanico:
            print(f"✅ Verificado en BD: {mecanico.nombre}")
        else:
            print("❌ No encontrado en BD")
    else:
        print(f"❌ Error en API: {response.status_code}")
    
    # Test 2: Crear mecánico duplicado (debería devolver el existente)
    response2 = client.post('/documentos/api/crear_mecanico/', {
        'nombre': 'Carlos Mecánico Test'
    })
    
    print(f"\n📤 POST /api/crear_mecanico/ con nombre duplicado")
    print(f"📊 Status: {response2.status_code}")
    print(f"📄 Response: {response2.content.decode()}")
    
    # Test 3: Endpoint de autocomplete
    response3 = client.get('/autocomplete/mecanico/', {
        'q': 'Carlos'
    })
    
    print(f"\n📤 GET /autocomplete/mecanico/ con q=Carlos")
    print(f"📊 Status: {response3.status_code}")
    print(f"📄 Response: {response3.content.decode()}")
    
    print("\n📋 RESUMEN:")
    print(f"   Total mecánicos en BD: {Mecanico.objects.count()}")
    for mec in Mecanico.objects.all():
        print(f"   - ID {mec.id}: {mec.nombre}")

def test_mecanicos_existentes():
    """Listar mecánicos existentes"""
    print("\n🔍 MECÁNICOS EXISTENTES:")
    mecanicos = Mecanico.objects.all()
    if mecanicos.exists():
        for mec in mecanicos:
            print(f"   - ID {mec.id}: {mec.nombre}")
    else:
        print("   (No hay mecánicos en la base de datos)")

if __name__ == "__main__":
    test_mecanicos_existentes()
    test_crear_mecanico_api()
