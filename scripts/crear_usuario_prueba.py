#!/usr/bin/env python
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.contrib.auth.models import User
from django.test import Client

from taller.models.clientes import Cliente
from taller.models.empresa import Empresa
from taller.models.vehiculos import Vehiculo


def crear_y_probar():
    # Crear o obtener usuario de prueba
    user, created = User.objects.get_or_create(
        username="test_vehiculos",
        defaults={"email": "test@test.com", "password": "test123"},
    )
    if created:
        user.set_password("test123")
        user.save()

    # Crear o obtener empresa
    empresa, _ = Empresa.objects.get_or_create(
        user=user, defaults={"nombre_taller": "Test Garage CL", "pais": "CL"}
    )

    print(f"✅ Usuario: {user.username}")
    print(f"✅ Empresa: {empresa.nombre_taller} ({empresa.pais})")

    # Contar clientes y vehículos
    clientes = Cliente.objects.filter(empresa=empresa)
    print(f"✅ Clientes: {clientes.count()}")

    if clientes.exists():
        cliente = clientes.first()
        vehiculos = Vehiculo.objects.filter(cliente=cliente)
        print(f"✅ Vehículos del cliente {cliente.nombre}: {vehiculos.count()}")

        # Probar la API
        client = Client()
        client.force_login(user)
        response = client.get(f"/cl/documentos/api/vehiculos-cliente/?cliente_id={cliente.id}")
        print(f"✅ API Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Response: {len(data.get('vehiculos', []))} vehículos")

    print("\n🎯 Para probar:")
    print(f"   1. Login: {user.username} / test123")
    print("   2. URL: http://localhost:8000/cl/documentos/nuevo/")


if __name__ == "__main__":
    crear_y_probar()
