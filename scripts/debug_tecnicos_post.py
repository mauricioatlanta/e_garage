#!/usr/bin/env python
"""
Script para verificar los campos POST que se están enviando desde el formulario
"""

import os
import sys

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from taller.models.empresa import Empresa
from taller.models.tecnico import Tecnico


def verificar_POST_debug():
    print("🔍 Verificando configuración POST para técnicos...")

    # Verificar empresas
    empresas = Empresa.objects.all()
    if empresas.exists():
        empresa = empresas.first()
        print(f"✅ Empresa de prueba: {empresa.nombre_taller} (ID: {empresa.id})")

        # Simular datos POST como los envía el formulario
        datos_post = {
            "nombre": "Juan Pérez",
            "telefono": "+56912345678",
            "direccion": "Calle Falsa 123",
        }

        print(f"📋 Datos de prueba: {datos_post}")

        # Simular la lógica de la vista
        nombre = datos_post.get("nombre", "").strip()
        telefono = datos_post.get("telefono", "").strip()
        direccion = datos_post.get("direccion", "").strip()

        print(f"🔍 Nombre procesado: '{nombre}' (longitud: {len(nombre)})")
        print(f"🔍 Condición len(nombre.strip()) >= 2: {len(nombre.strip()) >= 2}")
        print(
            f"🔍 Condición nombre and len(nombre.strip()) >= 2: {nombre and len(nombre.strip()) >= 2}"
        )

        # Verificar si ya existe
        existe = Tecnico.objects.filter(empresa=empresa, nombre__iexact=nombre).exists()
        print(f"🔍 ¿Ya existe técnico con este nombre? {existe}")

        if nombre and len(nombre.strip()) >= 2 and not existe:
            print("✅ Todas las validaciones pasaron - debería crear el técnico")

            try:
                tecnico = Tecnico.objects.create(
                    empresa=empresa,
                    nombre=nombre,
                    telefono=telefono,
                    direccion=direccion,
                    activo=True,
                )
                print(f"✅ Técnico creado exitosamente: {tecnico.nombre} (ID: {tecnico.id})")

                # Limpiar
                tecnico.delete()
                print("🗑️ Técnico de prueba eliminado")

            except Exception as e:
                print(f"❌ Error al crear técnico: {e}")
        else:
            print("❌ Las validaciones no pasaron")
            if not nombre:
                print("  - Nombre vacío")
            elif len(nombre.strip()) < 2:
                print("  - Nombre muy corto")
            elif existe:
                print("  - Ya existe técnico con ese nombre")

    else:
        print("❌ No hay empresas disponibles")


if __name__ == "__main__":
    verificar_POST_debug()
