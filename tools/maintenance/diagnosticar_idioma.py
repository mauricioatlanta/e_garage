#!/usr/bin/env python
"""
Script para diagnosticar el problema de idiomas
"""

import os

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.contrib.auth.models import User
from django.test import RequestFactory


def diagnosticar_idioma():
    """Diagnostica el problema de configuración de idiomas"""
    print("🔍 DIAGNÓSTICO DE CONFIGURACIÓN DE IDIOMAS")
    print("=" * 60)

    # Crear un request factory para simular requests
    factory = RequestFactory()

    # Simular request a /taller/clientes/ (sin prefijo de país)
    request = factory.get("/taller/clientes/")

    # Simular usuario autenticado de USA
    try:
        user_usa = User.objects.get(username="testuser_usa")
        request.user = user_usa

        print(f"👤 Usuario: {user_usa.username}")
        print(
            f"🏢 Empresa: {user_usa.empresa.nombre_taller if hasattr(user_usa, 'empresa') else 'Sin empresa'}"
        )
        print(
            f"🌍 País empresa: {user_usa.empresa.pais if hasattr(user_usa, 'empresa') else 'N/A'}"
        )

        # Simular el proceso de detección de país
        if hasattr(user_usa, "empresa") and user_usa.empresa:
            user_country = user_usa.empresa.pais
        else:
            user_country = None

        print(f"📍 País detectado: {user_country}")

        # Simular la lógica de idioma
        if user_country == "US":
            expected_lang = "en"
        elif user_country == "CL":
            expected_lang = "es"
        else:
            expected_lang = "es"

        print(f"🗣️ Idioma esperado: {expected_lang}")

    except User.DoesNotExist:
        print("❌ Usuario testuser_usa no encontrado")

    print("\n📋 CONFIGURACIÓN ACTUAL:")
    print(f"   • LANGUAGES: {django.conf.settings.LANGUAGES}")
    print(f"   • LANGUAGE_CODE: {django.conf.settings.LANGUAGE_CODE}")
    print(f"   • LANGUAGE_COOKIE_NAME: {django.conf.settings.LANGUAGE_COOKIE_NAME}")

    print("\n🔧 MIDDLEWARES ACTIVOS:")
    middlewares = django.conf.settings.MIDDLEWARE
    for i, middleware in enumerate(middlewares):
        if "language" in middleware.lower() or "i18n" in middleware.lower():
            print(f"   {i+1}. {middleware}")

    print("\n✅ DIAGNÓSTICO COMPLETADO!")


if __name__ == "__main__":
    diagnosticar_idioma()
