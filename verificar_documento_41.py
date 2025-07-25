#!/usr/bin/env python
"""
Verificar el documento ID 41 y sus datos relacionados
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'e_garage.settings')

import django
from django.conf import settings

settings.DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

django.setup()

from taller.models.documento import Documento
from taller.models.clientes import Cliente
from taller.models.vehiculos import Vehiculo

def verificar_documento_41():
    print("=== VERIFICACIÓN DOCUMENTO ID 41 ===\n")
    
    try:
        # Obtener el documento
        doc = Documento.objects.get(id=41)
        print(f"📄 Documento encontrado:")
        print(f"   ID: {doc.id}")
        print(f"   Número: {doc.numero_documento}")
        print(f"   Tipo: {doc.tipo_documento}")
        print(f"   Empresa: {doc.empresa.nombre_taller}")
        print(f"   Cliente: {doc.cliente}")
        print(f"   Vehículo: {doc.vehiculo}")
        
        # Verificar cliente
        cliente = doc.cliente
        print(f"\n👤 Cliente asociado:")
        print(f"   ID: {cliente.id}")
        print(f"   Nombre: {cliente.nombre} {cliente.apellido}")
        print(f"   Empresa: {cliente.empresa.nombre_taller}")
        
        # Verificar vehículos del cliente
        vehiculos_cliente = Vehiculo.objects.filter(cliente=cliente)
        print(f"\n🚗 Vehículos del cliente ({vehiculos_cliente.count()}):")
        for vehiculo in vehiculos_cliente:
            print(f"   - ID {vehiculo.id}: {vehiculo.patente} - {vehiculo.marca.nombre} {vehiculo.modelo.nombre}")
        
        # Verificar todos los vehículos de la empresa
        vehiculos_empresa = Vehiculo.objects.filter(cliente__empresa=doc.empresa)
        print(f"\n🏢 Todos los vehículos de la empresa ({vehiculos_empresa.count()}):")
        for vehiculo in vehiculos_empresa:
            print(f"   - ID {vehiculo.id}: {vehiculo.patente} - {vehiculo.marca.nombre} {vehiculo.modelo.nombre} (Cliente: {vehiculo.cliente.nombre})")
        
        # Verificar si el vehículo del documento pertenece al cliente
        if doc.vehiculo:
            if doc.vehiculo.cliente == doc.cliente:
                print(f"\n✅ El vehículo del documento pertenece al cliente correcto")
            else:
                print(f"\n❌ PROBLEMA: El vehículo del documento NO pertenece al cliente")
                print(f"   Vehículo cliente: {doc.vehiculo.cliente}")
                print(f"   Documento cliente: {doc.cliente}")
        else:
            print(f"\n⚠️ El documento no tiene vehículo asignado")
            
    except Documento.DoesNotExist:
        print("❌ Documento ID 41 no encontrado")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verificar_documento_41()
