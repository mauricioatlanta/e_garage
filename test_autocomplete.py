#!/usr/bin/env python
import os
import sys
import django
import requests

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

def test_autocomplete_endpoints():
    """Prueba los endpoints de autocompletado"""
    base_url = "http://127.0.0.1:8000"
    
    # URLs a probar
    urls = [
        f"{base_url}/documentos/autocomplete/cliente/",
        f"{base_url}/documentos/autocomplete/vehiculo/",
        f"{base_url}/documentos/autocomplete/servicio/"
    ]
    
    print("🔍 Probando endpoints de autocompletado...")
    
    for url in urls:
        try:
            print(f"\n📡 Probando: {url}")
            response = requests.get(url, timeout=5)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Resultados: {len(data.get('results', []))}")
                if data.get('results'):
                    print(f"   Primer resultado: {data['results'][0]}")
            else:
                print(f"   Error: {response.text[:100]}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

def test_cliente_vehiculos():
    """Prueba específica de cliente y sus vehículos"""
    from taller.models.clientes import Cliente
    from taller.models.vehiculos import Vehiculo
    
    print("\n🚗 Probando relación cliente-vehículos...")
    
    try:
        # Buscar cliente Ricardo Lunari
        cliente = Cliente.objects.filter(nombre__icontains="Ricardo").first()
        if cliente:
            print(f"✅ Cliente encontrado: {cliente.nombre} {cliente.apellido or ''}")
            print(f"   ID: {cliente.pk}")
            print(f"   Empresa: {cliente.empresa}")
            
            # Buscar vehículos del cliente
            vehiculos = Vehiculo.objects.filter(cliente=cliente)
            print(f"   Vehículos: {vehiculos.count()}")
            for v in vehiculos:
                print(f"     - {v.patente} ({v.marca} {v.modelo})")
                
            # Probar URL de vehículos
            url = f"http://127.0.0.1:8000/documentos/autocomplete/vehiculo/?cliente={cliente.pk}"
            print(f"\n📡 Probando URL vehículos: {url}")
            response = requests.get(url)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Vehículos encontrados: {len(data.get('results', []))}")
                for resultado in data.get('results', []):
                    print(f"     - {resultado}")
        else:
            print("❌ Cliente Ricardo no encontrado")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_autocomplete_endpoints()
    test_cliente_vehiculos()
