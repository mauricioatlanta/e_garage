#!/usr/bin/env python
"""
Script de debug para verificar el problema de DAL forward
"""

import os

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client

from taller.forms.documento_form import DocumentoForm
from taller.models.clientes import Cliente
from taller.models.empresa import Empresa
from taller.models.vehiculos import Vehiculo

User = get_user_model()


def debug_dal_forward():
    print("🔍 DEBUG: Verificando DAL Forward para US")
    print("=" * 50)

    # 1. Verificar si hay usuarios y empresas
    users = User.objects.all()
    print(f"👥 Usuarios encontrados: {users.count()}")

    empresas = Empresa.objects.all()
    print(f"🏢 Empresas encontradas: {empresas.count()}")

    if not users.exists():
        print("❌ No hay usuarios. Crear uno primero.")
        return

    if not empresas.exists():
        print("❌ No hay empresas. Crear una primero.")
        return

    # 2. Crear datos de prueba si no existen
    user = users.first()
    empresa = empresas.first()

    print(f"👤 Usando usuario: {user.username}")
    print(f"🏢 Usando empresa: {empresa.nombre_taller} (país: {getattr(empresa, 'pais', 'CL')})")

    # 3. Crear cliente de prueba si no existe
    cliente, created = Cliente.objects.get_or_create(
        empresa=empresa,
        nombre="Cliente Test US",
        defaults={"email": "test@example.com", "telefono": "123456789"},
    )
    print(f"👤 Cliente: {cliente.nombre} (creado: {created})")

    # 4. Crear vehículos de prueba si no existen
    vehiculos = Vehiculo.objects.filter(cliente=cliente, empresa=empresa)
    if not vehiculos.exists():
        from taller.models.marca import Marca
        from taller.models.modelo import Modelo

        marca, _ = Marca.objects.get_or_create(nombre="Toyota", country=empresa.pais or "CL")

        modelo, _ = Modelo.objects.get_or_create(
            nombre="Corolla", marca=marca, country=empresa.pais or "CL"
        )

        vehiculo = Vehiculo.objects.create(
            cliente=cliente,
            empresa=empresa,
            patente="ABC123",
            marca=marca,
            modelo=modelo,
            anio=2020,
        )
        print(f"🚗 Vehículo creado: {vehiculo.patente}")
    else:
        print(f"🚗 Vehículos existentes: {vehiculos.count()}")
        for v in vehiculos:
            print(f"   - {v.patente} ({v.marca.nombre if v.marca else 'Sin marca'})")

    # 5. Probar el form con country="US"
    print("\n📝 Probando DocumentoForm con country='US'...")
    form = DocumentoForm(country="US", empresa=empresa, user=user)

    print(f"🌍 Country del form: {form.country}")
    print(f"🔗 URL cliente: {form.fields['cliente'].widget.url}")
    print(f"🔗 URL vehículo: {form.fields['vehiculo'].widget.url}")

    # 6. Probar autocomplete endpoint
    print("\n🌐 Probando endpoint de autocomplete...")
    client = Client()

    # Login
    client.force_login(user)

    # Probar autocomplete de vehículos con cliente
    url = "/us/autocomplete/vehiculo/"
    response = client.get(url)
    print(f"📡 GET {url} - Status: {response.status_code}")

    if response.status_code == 200:
        print(f"📄 Response: {response.content.decode()[:200]}...")
    else:
        print(f"❌ Error: {response.content.decode()}")

    # Probar con cliente específico
    url_with_cliente = f"/us/autocomplete/vehiculo/?cliente={cliente.id}"
    response = client.get(url_with_cliente)
    print(f"📡 GET {url_with_cliente} - Status: {response.status_code}")

    if response.status_code == 200:
        print(f"📄 Response con cliente: {response.content.decode()[:200]}...")
    else:
        print(f"❌ Error con cliente: {response.content.decode()}")


if __name__ == "__main__":
    debug_dal_forward()
