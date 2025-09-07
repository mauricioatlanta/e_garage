#!/usr/bin/env python
"""
Script para mostrar documentos accesibles y crear uno de prueba si es necesario
"""
import os

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.contrib.auth.models import User

from taller.documentos.models import Documento
from taller.models import Empresa
from taller.models.clientes import Cliente
from taller.models.vehiculos import Vehiculo


def main():
    print("=== ANÁLISIS DE DOCUMENTOS ACCESIBLES ===")

    # Mostrar todos los usuarios y sus documentos
    for user in User.objects.all():
        try:
            empresa = user.empresa
            docs = Documento.objects.filter(empresa=empresa)
            print(f"\n👤 Usuario: {user.username}")
            print(f"   Empresa: {empresa.nombre_taller} (ID: {empresa.pk})")
            print(f"   Documentos: {docs.count()}")

            if docs.exists():
                for doc in docs[:3]:
                    print(f"   - Documento {doc.pk}: {doc.tipo} - {doc.estado}")
                    print(
                        f"     URL: http://127.0.0.1:8000/us/documentos/form/{doc.pk}/"
                    )
            else:
                print("   - Sin documentos")

        except Exception as e:
            print(f"\n👤 Usuario: {user.username} (Sin empresa: {e})")

    # Crear un documento de prueba para el usuario admin si no tiene
    try:
        admin_user = User.objects.get(username="admin")
        admin_empresa = admin_user.empresa

        # Verificar si tiene documentos
        admin_docs = Documento.objects.filter(empresa=admin_empresa)
        if not admin_docs.exists():
            print(f"\n🔧 Creando documento de prueba para {admin_user.username}...")

            # Crear cliente de prueba si no existe
            cliente, created = Cliente.objects.get_or_create(
                empresa=admin_empresa,
                nombre="Cliente de Prueba",
                defaults={
                    "apellido": "Test",
                    "email": "test@example.com",
                    "telefono": "123456789",
                },
            )

            # Crear vehículo de prueba si no existe
            vehiculo, created = Vehiculo.objects.get_or_create(
                empresa=admin_empresa,
                placa="TEST123",
                defaults={
                    "marca": "Toyota",
                    "modelo": "Corolla",
                    "ano": 2020,
                    "cliente": cliente,
                },
            )

            # Crear documento
            documento = Documento.objects.create(
                empresa=admin_empresa,
                tipo="PRES",
                estado="DRAFT",
                cliente=cliente,
                vehiculo=vehiculo,
                subtotal=0,
                impuestos=0,
                total=0,
            )

            print(f"✅ Documento creado: ID {documento.pk}")
            print(f"   URL: http://127.0.0.1:8000/us/documentos/form/{documento.pk}/")

    except Exception as e:
        print(f"\n❌ Error creando documento para admin: {e}")


if __name__ == "__main__":
    main()
