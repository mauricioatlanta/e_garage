#!/usr/bin/env python
"""
Diagnóstico de redirección de URLs por país para usuarios de Chile
"""
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.contrib.auth.models import User
from django.test import Client

from taller.models.empresa import Empresa


def diagnosticar_redireccion():
    print("=== DIAGNÓSTICO DE REDIRECCIÓN POR PAÍS ===\n")

    # Obtener todos los usuarios con empresa
    usuarios_con_empresa = User.objects.filter(empresa__isnull=False)

    print(f"Usuarios con empresa encontrados: {usuarios_con_empresa.count()}")

    for user in usuarios_con_empresa[:5]:
        print(f"\n--- Usuario: {user.username} ---")
        print(f"Empresa: {user.empresa.nombre_taller}")
        print(f"País de empresa: {user.empresa.pais}")
        print(f"es_chile: {user.empresa.es_chile}")
        print(f"es_usa: {user.empresa.es_usa}")

        # Crear cliente y simular login
        client = Client()
        client.force_login(user)

        print("\nProbando accesos a documentos:")

        # Probar acceso directo a Chile
        response = client.get("/cl/documentos/form/", follow=False)
        print(f"  /cl/documentos/form/ → Status: {response.status_code}")
        if response.status_code == 302:
            print(f"    Redirige a: {response.get('Location', 'N/A')}")

        # Probar acceso directo a USA
        response = client.get("/us/documentos/form/", follow=False)
        print(f"  /us/documentos/form/ → Status: {response.status_code}")
        if response.status_code == 302:
            print(f"    Redirige a: {response.get('Location', 'N/A')}")

        # Probar acceso genérico a documentos
        response = client.get("/documentos/", follow=False)
        print(f"  /documentos/ → Status: {response.status_code}")
        if response.status_code == 302:
            print(f"    Redirige a: {response.get('Location', 'N/A')}")

        print(
            f"\n  🎯 URL esperada para este usuario: /{'cl' if user.empresa.pais == 'CL' else 'us'}/documentos/form/"
        )
        break  # Solo probar con el primer usuario para no saturar


def encontrar_problema_url():
    print("\n=== ANÁLISIS DE CONFIGURACIÓN DE URLS ===\n")

    # Revisar configuración de URLs principales
    from django.test import RequestFactory
    from django.urls import reverse

    factory = RequestFactory()

    print("1. URLs de documentos disponibles:")
    try:
        # Intentar generar URLs
        url_cl = reverse("documentos_cl:documento_crear")
        print(f"  documentos_cl:documento_crear → {url_cl}")
    except Exception as e:
        print(f"  ❌ documentos_cl:documento_crear → Error: {e}")

    try:
        url_us = reverse("documentos_us:documento_crear")
        print(f"  documentos_us:documento_crear → {url_us}")
    except Exception as e:
        print(f"  ❌ documentos_us:documento_crear → Error: {e}")

    print("\n2. URLs genéricas:")
    try:
        from django.conf import settings

        print(f"  DEBUG: {settings.DEBUG}")
        print(
            f"  DEFAULT_COUNTRY: {getattr(settings, 'DEFAULT_COUNTRY', 'No definido')}"
        )
    except Exception as e:
        print(f"  Error obteniendo configuración: {e}")


def probar_deteccion_pais():
    print("\n=== PRUEBA DE DETECCIÓN DE PAÍS ===\n")

    from django.test import RequestFactory

    from taller.middleware.country_context import CountryContextMiddleware

    factory = RequestFactory()
    middleware = CountryContextMiddleware(lambda r: None)

    urls_prueba = [
        "/cl/documentos/form/",
        "/us/documentos/form/",
        "/documentos/form/",
        "/cl/",
        "/us/",
        "/",
    ]

    for url in urls_prueba:
        request = factory.get(url)
        request.user = User.objects.first()  # Usuario de prueba

        middleware.process_request(request)

        country = getattr(request, "country", "N/A")
        print(f"  {url:25} → País detectado: {country}")


if __name__ == "__main__":
    diagnosticar_redireccion()
    encontrar_problema_url()
    probar_deteccion_pais()
