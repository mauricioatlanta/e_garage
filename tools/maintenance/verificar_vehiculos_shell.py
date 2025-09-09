#!/usr/bin/env python3
"""
Test simple de la creación de vehículos usando manage.py shell
"""

import subprocess
import sys


def test_vehiculo_creacion():
    print("🧪 Test Simple - Verificación Vista Vehículos")
    print("=" * 60)
    
    # Script para ejecutar en shell de Django
    shell_script = '''
from django.contrib.auth.models import User
from taller.models.clientes import Cliente
from taller.models.marca import Marca
from taller.models.modelo import Modelo
from taller.models.extras_vehiculo import ColorVehiculo
from taller.models.vehiculos import Vehiculo

print("Verificando disponibilidad de datos...")

# Obtener usuario test
try:
    user = User.objects.get(username='testuser')
    print(f"Usuario: {user.username}")
    
    # Verificar empresa
    if hasattr(user, 'empresa'):
        print(f"Empresa: {user.empresa.nombre_taller}")
    else:
        print("Usuario sin empresa asignada")
        
except User.DoesNotExist:
    print("Usuario testuser no encontrado")
    user = None

if user and hasattr(user, 'empresa'):
    # Contar datos disponibles
    clientes = Cliente.objects.filter(empresa=user.empresa)
    marcas = Marca.objects.all()
    modelos = Modelo.objects.all()
    colores = ColorVehiculo.objects.all()
    vehiculos = Vehiculo.objects.filter(empresa=user.empresa)
    
    print(f"\\nDatos disponibles:")
    print(f"  Clientes: {clientes.count()}")
    print(f"  Marcas: {marcas.count()}")
    print(f"  Modelos: {modelos.count()}")
    print(f"  Colores: {colores.count()}")
    print(f"  Vehiculos existentes: {vehiculos.count()}")
    
    # Verificar si hay datos mínimos
    if all([clientes.exists(), marcas.exists(), modelos.exists(), colores.exists()]):
        print("\\nDATOS SUFICIENTES para crear vehiculos")
        
        # Mostrar datos específicos
        cliente = clientes.first()
        marca = marcas.first()
        modelo = modelos.filter(marca=marca).first() or modelos.first()
        color = colores.first()
        
        print(f"\\nDatos para test:")
        print(f"  Cliente: {cliente.nombre} (ID: {cliente.id})")
        print(f"  Marca: {marca.nombre} (ID: {marca.id})")
        if modelo:
            print(f"  Modelo: {modelo.nombre} (ID: {modelo.id})")
        print(f"  Color: {color.nombre} (ID: {color.id})")
        
        print(f"\\nCampos del modelo Vehiculo:")
        vehiculo_fields = Vehiculo._meta.get_fields()
        for field in vehiculo_fields:
            print(f"  {field.name}: {type(field).__name__}")
            
    else:
        print("\\nDATOS INSUFICIENTES para crear vehiculos")

print("\\nVerificacion completada")
'''
    
    print("🚀 Ejecutando verificación en shell de Django...")
    
    try:
        # Ejecutar shell script
        result = subprocess.run([
            sys.executable, 'manage.py', 'shell', '-c', shell_script
        ], capture_output=True, text=True, cwd='e:\\projecto\\e_garage')
        
        print("\n📄 Salida del shell:")
        print(result.stdout)
        
        if result.stderr:
            print("\n⚠️ Errores:")
            print(result.stderr)
            
        if result.returncode == 0:
            print("\n✅ Test ejecutado exitosamente")
        else:
            print(f"\n❌ Test falló con código: {result.returncode}")
            
    except Exception as e:
        print(f"❌ Error ejecutando test: {e}")

if __name__ == '__main__':
    test_vehiculo_creacion()
