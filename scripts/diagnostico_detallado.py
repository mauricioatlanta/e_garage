#!/usr/bin/env python
"""
Diagnóstico del problema de enrutamiento por país - Versión detallada
"""

import os
import sys

import django

# Configurar Django
sys.path.append("/projecto/e_garage")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")

try:
    django.setup()
except Exception as e:
    print(f"❌ Error configurando Django: {e}")
    exit(1)

from django.contrib.auth import get_user_model
from django.test import Client

User = get_user_model()


def diagnosticar_problema_usa():
    """Diagnosticar por qué el cliente chileno llega a /us/documentos/form/"""
    print("=== DIAGNÓSTICO PROBLEMA USA ===\n")

    client = Client()

    # Obtener usuario chileno
    try:
        user_cl = User.objects.get(username="testuser_cl")
        print(f"👤 Usuario: {user_cl.username}")

        try:
            if hasattr(user_cl, "empresa") and user_cl.empresa:
                empresa = user_cl.empresa
                print(f"🏢 Empresa: {empresa.nombre} (ID: {empresa.id})")
                print(f"🌎 País empresa: {empresa.pais}")
                print(f"🇨🇱 Es Chile: {empresa.es_chile()}")
                print(f"🇺🇸 Es USA: {empresa.es_usa()}")
            else:
                print("⚠️  Usuario sin empresa asignada directamente")
        except Exception as e:
            print(f"⚠️  Error al obtener empresa: {e}")

        # Iniciar sesión
        client.force_login(user_cl)
        print("✅ Sesión iniciada\n")

    except User.DoesNotExist:
        print("❌ Usuario testuser_cl no encontrado")
        return

    # Probar diferentes rutas para ver cuál lleva a /us/
    rutas_a_probar = [
        ("/", "Página principal"),
        ("/cl/", "Chile home"),
        ("/cl/documentos/", "Documentos Chile"),
        ("/cl/documentos/nuevo/", "Crear documento Chile"),
        ("/documentos/", "Documentos genérico"),
        ("/taller/documentos/", "Taller documentos"),
    ]

    for ruta, descripcion in rutas_a_probar:
        print(f"🔍 Probando: {descripcion} ({ruta})")
        response = client.get(ruta, follow=False)

        print(f"   Status: {response.status_code}")

        if response.status_code in [301, 302]:
            location = response.get("Location", "No location header")
            print(f"   Redirige a: {location}")

            # Si redirige a /us/, ¡encontramos el problema!
            if "/us/" in location:
                print("   🚨 ¡PROBLEMA ENCONTRADO! Redirige a USA")

                # Seguir la redirección para ver el resultado final
                response_final = client.get(ruta, follow=True)
                if response_final.redirect_chain:
                    print("   Cadena completa de redirecciones:")
                    for redirect_url, redirect_status in response_final.redirect_chain:
                        print(f"     → {redirect_status}: {redirect_url}")
                        if "/us/" in redirect_url:
                            print("       ⚠️  Esta es la redirección problemática")

        elif response.status_code == 200:
            print("   ✅ Carga directamente")
        else:
            print(f"   ⚠️  Error: {response.status_code}")

        print()

    # Probar la búsqueda de clientes también
    print("=== PRUEBA BÚSQUEDA AJAX ===\n")

    ajax_urls = [
        "/ajax/clientes/buscar/?q=test&page=1",
        "/cl/ajax/clientes/buscar/?q=test&page=1",
        "/us/ajax/clientes/buscar/?q=test&page=1",
        "/taller/ajax/clientes/buscar/?q=test&page=1",
    ]

    for url in ajax_urls:
        print(f"🔍 AJAX: {url}")
        response = client.get(url)
        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            try:
                import json

                data = json.loads(response.content)
                print(f"   ✅ Respuesta JSON: {len(data.get('results', []))} clientes encontrados")
            except:
                print("   ⚠️  Respuesta no es JSON válido")
        elif response.status_code == 404:
            print("   ❌ URL no encontrada")
        else:
            print(f"   ⚠️  Error: {response.status_code}")
        print()


if __name__ == "__main__":
    diagnosticar_problema_usa()
