import os
import django
import sys
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings_sqlite')
django.setup()

from taller.models.tecnico import Mecanico
from django.contrib.auth.models import User
import requests

def test_crear_mecanico_directo():
    """Test directo sin usar Django Client para evitar middleware"""
    
    print("🧪 TESTING: Crear Mecánico Directo")
    
    # Test 1: Verificar mecánicos existentes
    print(f"📊 Mecánicos existentes: {Tecnico.objects.count()}")
    
    # Test 2: Crear mecánico directamente
    try:
        mecanico, created = Tecnico.objects.get_or_create(
            nombre="Test Mecánico API"
        )
        
        if created:
            print(f"✅ Mecánico creado: ID {mecanico.id}, Nombre: {mecanico.nombre}")
        else:
            print(f"ℹ️ Mecánico existente: ID {mecanico.id}, Nombre: {mecanico.nombre}")
            
    except Exception as e:
        print(f"❌ Error al crear mecánico: {e}")
    
    # Test 3: Probar el endpoint con requests
    try:
        # Necesitamos obtener CSRF token primero
        session = requests.Session()
        
        # Obtener la página de login para el CSRF token
        login_url = 'http://127.0.0.1:8000/admin/login/'
        response = session.get(login_url)
        
        if 'csrftoken' in session.cookies:
            csrf_token = session.cookies['csrftoken']
            print(f"🔑 CSRF Token obtenido: {csrf_token[:10]}...")
            
            # Intentar crear mecánico via API
            api_url = 'http://127.0.0.1:8000/documentos/api/crear_mecanico/'
            data = {
                'nombre': 'Test Mecánico HTTP',
                'csrfmiddlewaretoken': csrf_token
            }
            
            response = session.post(api_url, data=data)
            print(f"📤 POST {api_url}")
            print(f"📊 Status: {response.status_code}")
            print(f"📄 Response: {response.text[:200]}...")
            
        else:
            print("❌ No se pudo obtener CSRF token")
            
    except Exception as e:
        print(f"❌ Error en test HTTP: {e}")
    
    # Test 4: Listar todos los mecánicos finales
    print(f"\n📋 TOTAL MECÁNICOS: {Tecnico.objects.count()}")
    for mec in Tecnico.objects.all()[:10]:  # Solo los primeros 10
        print(f"   - ID {mec.id}: {mec.nombre}")

if __name__ == "__main__":
    test_crear_mecanico_directo()
