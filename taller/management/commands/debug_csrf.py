#!/usr/bin/env python
"""
Comando Django para debuggear configuraciones CSRF.
"""

import os

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Debuggear configuraciones CSRF"

    def handle(self, *args, **options):
        self.stdout.write("🔍 Debugging CSRF configurations...")

        # Mostrar variables de entorno
        self.stdout.write("📝 Variables de entorno:")
        csrf_env = os.getenv("DJANGO_CSRF_TRUSTED_ORIGINS", "")
        self.stdout.write(f'  - DJANGO_CSRF_TRUSTED_ORIGINS: "{csrf_env}"')

        # Mostrar DEBUG
        self.stdout.write(f"  - DEBUG: {settings.DEBUG}")

        # Mostrar ALLOWED_HOSTS
        self.stdout.write(f"  - ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")

        # Mostrar CSRF_TRUSTED_ORIGINS
        self.stdout.write(f"  - CSRF_TRUSTED_ORIGINS: {settings.CSRF_TRUSTED_ORIGINS}")
        self.stdout.write(f"  - CSRF_TRUSTED_ORIGINS type: {type(settings.CSRF_TRUSTED_ORIGINS)}")
        self.stdout.write(f"  - CSRF_TRUSTED_ORIGINS len: {len(settings.CSRF_TRUSTED_ORIGINS)}")
        self.stdout.write(f"  - CSRF_TRUSTED_ORIGINS bool: {bool(settings.CSRF_TRUSTED_ORIGINS)}")

        # Mostrar otras configuraciones CSRF
        self.stdout.write("⚙️ Otras configuraciones CSRF:")
        self.stdout.write(
            f'  - CSRF_COOKIE_HTTPONLY: {getattr(settings, "CSRF_COOKIE_HTTPONLY", "No definido")}'
        )
        self.stdout.write(
            f'  - CSRF_COOKIE_SAMESITE: {getattr(settings, "CSRF_COOKIE_SAMESITE", "No definido")}'
        )
        self.stdout.write(
            f'  - CSRF_USE_SESSIONS: {getattr(settings, "CSRF_USE_SESSIONS", "No definido")}'
        )
        self.stdout.write(
            f'  - CSRF_COOKIE_SECURE: {getattr(settings, "CSRF_COOKIE_SECURE", "No definido")}'
        )

        # Verificar middleware
        csrf_middleware = "django.middleware.csrf.CsrfViewMiddleware"
        self.stdout.write(f"🛡️ Middleware CSRF: {csrf_middleware in settings.MIDDLEWARE}")

        self.stdout.write("✅ Debug completado.")
