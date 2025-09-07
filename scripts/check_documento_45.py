#!/usr/bin/env python
"""
Script para verificar el estado del documento 45 y los usuarios
"""
import os

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.contrib.auth.models import User

from taller.documentos.models import Documento
from taller.models import Empresa


def main():
    print("=== ANÁLISIS DEL DOCUMENTO 45 ===")

    # Verificar si el documento existe
    try:
        documento = Documento.objects.get(pk=45)
        print("✓ Documento 45 existe")
        print(f"  - Empresa ID: {documento.empresa.id}")
        print(f"  - Empresa nombre: {documento.empresa.nombre_taller}")
        print(f"  - Usuario de la empresa: {documento.empresa.user.username}")
        print(f"  - Tipo: {documento.tipo}")
        print(f"  - Estado: {documento.estado}")
    except Documento.DoesNotExist:
        print("✗ Documento 45 no existe")
        return

    print("\n=== USUARIOS DISPONIBLES ===")
    users = User.objects.all()[:10]
    for user in users:
        try:
            empresa = user.empresa
            print(
                f"- {user.username} (ID: {user.id}) -> Empresa: {empresa.id} ({empresa.nombre_taller})"
            )
        except:
            print(f"- {user.username} (ID: {user.id}) -> Sin empresa")

    print("\n=== EMPRESAS DISPONIBLES ===")
    empresas = Empresa.objects.all()[:10]
    for empresa in empresas:
        print(
            f"- Empresa {empresa.id}: {empresa.nombre_taller} (Usuario: {empresa.user.username})"
        )


if __name__ == "__main__":
    main()
