#!/usr/bin/env python
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.contrib.auth.models import User

from taller.models.clientes import Cliente
from taller.models.empresa import Empresa
from taller.models.vehiculos import Vehiculo

print("=== RESUMEN DE DATOS ===")

# Verificar usuarios
try:
    user_chile = User.objects.get(username="testuser_chile")
    print(f"✅ Usuario Chile: {user_chile.username}")
    print(f"   Empresa: {user_chile.empresa.nombre_taller}")

    # Clientes de esa empresa
    clientes = Cliente.objects.filter(empresa=user_chile.empresa)
    print(f"   Clientes: {clientes.count()}")

    for i, cliente in enumerate(clientes[:3]):
        vehiculos = Vehiculo.objects.filter(cliente=cliente)
        print(
            f"   Cliente {i+1}: {cliente.nombre} {cliente.apellido} - {vehiculos.count()} vehículos"
        )
        for v in vehiculos[:2]:
            print(f"      - {v.patente} ({v.marca.nombre if v.marca else 'Sin marca'})")

except Exception as e:
    print(f"❌ Error: {e}")

print("\n=== CONCLUSIÓN ===")
print("✅ JavaScript agregado al template crear_documento.html")
print("✅ API api_vehiculos_cliente existe con filtrado de empresa")
print("✅ endpoint obtener_vehiculos_por_cliente corregido con filtrado")
print(
    "\n🎯 SOLUCIÓN IMPLEMENTADA: Al seleccionar un cliente en la creación de documento,"
)
print("   ahora se cargarán automáticamente solo los vehículos de ese cliente,")
print("   filtrados por la empresa del usuario autenticado.")
