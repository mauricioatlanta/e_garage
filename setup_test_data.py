#!/usr/bin/env python3
"""
Script rápido para crear datos de prueba y ejecutar diagnóstico
"""
import os

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone

from taller.models.clientes import Cliente
from taller.models.documento import Documento
from taller.models.empresa import Empresa


def crear_datos_prueba():
    """Crear datos mínimos para probar"""
    # Crear usuario si no existe
    user, created = User.objects.get_or_create(
        username="test_diagnostic",
        defaults={"email": "test@test.com", "password": "test123"},
    )
    print(f"Usuario: {user.username} (creado: {created})")

    # Crear empresa si no existe
    empresa, created = Empresa.objects.get_or_create(
        user=user, defaults={"nombre_taller": "Test Garage", "pais": "US"}
    )
    print(f"Empresa: {empresa.nombre_taller} (creado: {created})")

    # Crear cliente si no existe
    cliente, created = Cliente.objects.get_or_create(
        empresa=empresa,
        email="cliente@test.com",
        defaults={"nombre": "Cliente Test", "telefono": "123456789"},
    )
    print(f"Cliente: {cliente.nombre} (creado: {created})")

    # Crear documento de prueba si no existe
    doc, created = Documento.objects.get_or_create(
        empresa=empresa,
        tipo="PRES",
        numero=1,
        defaults={
            "fecha_emision": timezone.now().date(),
            "cliente": cliente,
            "country": "US",
            "moneda": "USD",
        },
    )
    print(f"Documento: {doc.tipo}-{doc.numero} (creado: {created})")

    return user, empresa, cliente, doc


if __name__ == "__main__":
    print("=== Creando datos de prueba ===")
    user, empresa, cliente, doc = crear_datos_prueba()

    print("\n=== Resumen ===")
    print(f"Usuario: {user.username}")
    print(f"Empresa: {empresa.nombre_taller} ({empresa.pais})")
    print(f"Documentos en empresa: {Documento.objects.filter(empresa=empresa).count()}")
    print(f"Clientes en empresa: {Cliente.objects.filter(empresa=empresa).count()}")

    print("\n=== Ejecutar comando probe ===")
    print(f"python manage.py probe_edit_document --user={user.username} --limit=1")
