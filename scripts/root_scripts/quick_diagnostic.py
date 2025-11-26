#!/usr/bin/env python
"""
Diagnóstico rápido de edición de documentos
"""

import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from taller.models import Documento


def main():
    print("=== DIAGNÓSTICO RÁPIDO DE EDICIÓN DE DOCUMENTOS ===")

    # Obtener usuario
    try:
        user = User.objects.get(username="admin")
    except User.DoesNotExist:
        user = User.objects.create_user(username="admin", password="admin123")
        print("✅ Usuario admin creado")

    print(f"Usuario: {user.username}")

    # Obtener documento de prueba
    doc = Documento.objects.filter(empresa__isnull=False).first()
    if not doc:
        print("❌ No hay documentos con empresa")
        return

    print(f"Documento: {doc.pk} - {doc.tipo}-{doc.numero}")
    print(f"Empresa: {doc.empresa.nombre_taller if doc.empresa else 'N/A'}")

    # Cliente de prueba
    client = Client()
    client.force_login(user)

    # URL de edición
    url = reverse("documentos:documento_editar", args=[doc.pk])
    print(f"URL: {url}")

    # GET primero
    print("\n--- GET REQUEST ---")
    response = client.get(url)
    print(f"Status: {response.status_code}")

    if response.status_code != 200:
        print("❌ Error en GET request")
        print(response.content.decode()[:500])
        return

    # POST con datos mínimos
    print("\n--- POST REQUEST ---")
    payload = {
        "tipo": doc.tipo,
        "fecha_emision": (doc.fecha_emision or timezone.now().date()).isoformat(),
        "cliente": getattr(doc.cliente, "pk", ""),
        "vehiculo": getattr(doc.vehiculo, "pk", ""),
        "tecnico_responsable": getattr(doc.tecnico_responsable, "pk", "") or "",
    }

    print(f"Payload: {payload}")

    response = client.post(url, payload)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        # Verificar si hay errores en el form
        if b"errorlist" in response.content:
            print("⚠️ Hay errores de formulario")
            # Extraer errores
            content = response.content.decode()
            import re

            errors = re.findall(r'<ul class="errorlist">(.*?)</ul>', content, re.DOTALL)
            for error in errors:
                print(f"Error: {error}")
        else:
            print("✅ Formulario renderizado sin errores aparentes")
    elif response.status_code == 302:
        print(f"✅ Redirección exitosa a: {response.get('Location', 'N/A')}")
    else:
        print(f"❌ Error HTTP: {response.status_code}")
        print(response.content.decode()[:500])


if __name__ == "__main__":
    main()
