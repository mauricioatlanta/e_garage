#!/usr/bin/env python
"""
Verificar clientes y vehículos disponibles para taller2
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "e_garage.settings")

import django
from django.conf import settings

settings.DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

django.setup()

from django.contrib.auth.models import User

from taller.models.clientes import Cliente
from taller.models.documento import Documento
from taller.models.perfilusuario import PerfilUsuario
from taller.models.vehiculos import Vehiculo


def verificar_datos_taller2():
    print("=== VERIFICACIÓN DATOS DISPONIBLES TALLER2 ===\n")

    # Obtener usuario y empresa
    user = User.objects.get(username="taller2")
    perfil = PerfilUsuario.objects.get(user=user)
    empresa = perfil.empresa

    print(f"👤 Usuario: {user.username}")
    print(f"🏢 Empresa: {empresa.nombre_taller} (ID: {empresa.pk})")

    # Verificar clientes
    clientes = Cliente.objects.filter(empresa=empresa)
    print(f"\n👥 Clientes disponibles para taller2: {clientes.count()}")
    for cliente in clientes[:5]:
        print(f"   - ID {cliente.pk}: {cliente.nombre} {cliente.apellido}")

    # Verificar vehículos
    vehiculos = Vehiculo.objects.filter(cliente__empresa=empresa)
    print(f"\n🚗 Vehículos disponibles para taller2: {vehiculos.count()}")
    for vehiculo in vehiculos[:5]:
        print(
            f"   - ID {vehiculo.pk}: {vehiculo.patente} - {vehiculo.marca.nombre} {vehiculo.modelo.nombre} (Cliente: {vehiculo.cliente.nombre})"
        )

    # Verificar documentos existentes para números únicos
    docs = Documento.objects.filter(empresa=empresa)
    print(f"\n📄 Documentos existentes: {docs.count()}")
    numeros_usados = [doc.numero_documento for doc in docs if doc.numero_documento]
    print(f"   Números de documento usados: {numeros_usados}")

    # Sugerir datos válidos para test
    if clientes.exists() and vehiculos.exists():
        cliente_valido = clientes.first()
        vehiculo_valido = vehiculos.filter(cliente=cliente_valido).first()

        print("\n✅ DATOS VÁLIDOS PARA TEST:")
        print(
            f"   Cliente ID: {cliente_valido.pk} ({cliente_valido.nombre} {cliente_valido.apellido})"
        )
        if vehiculo_valido:
            print(f"   Vehículo ID: {vehiculo_valido.pk} ({vehiculo_valido.patente})")
        else:
            print("   ⚠️ No hay vehículos para este cliente")
        print(f"   Número documento sugerido: TALLER2-TEST-{docs.count() + 1}")
    else:
        print("\n❌ PROBLEMA: No hay clientes o vehículos disponibles para taller2")


if __name__ == "__main__":
    verificar_datos_taller2()
