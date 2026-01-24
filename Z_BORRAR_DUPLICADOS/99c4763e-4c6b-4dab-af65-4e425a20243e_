#!/usr/bin/env python
"""
Comando Django para arreglar CSRF_TRUSTED_ORIGINS directamente.
"""

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Arregla CSRF_TRUSTED_ORIGINS directamente"

    def handle(self, *args, **options):
        self.stdout.write("🔧 Arreglando CSRF_TRUSTED_ORIGINS...")

        # Mostrar configuración actual
        self.stdout.write(f"📝 CSRF_TRUSTED_ORIGINS actual: {settings.CSRF_TRUSTED_ORIGINS}")
        self.stdout.write(f"📝 DEBUG: {settings.DEBUG}")

        # Modificar directamente las configuraciones
        if settings.DEBUG:
            # En desarrollo, agregar localhost y 127.0.0.1
            settings.CSRF_TRUSTED_ORIGINS = [
                "http://127.0.0.1:8000",
                "http://localhost:8000",
                "http://127.0.0.1:3000",
                "http://localhost:3000",
            ]
            self.stdout.write(
                f"✅ CSRF_TRUSTED_ORIGINS configurado para desarrollo: {settings.CSRF_TRUSTED_ORIGINS}"
            )
        else:
            # En producción, usar ALLOWED_HOSTS
            settings.CSRF_TRUSTED_ORIGINS = [
                f"https://{h}"
                for h in settings.ALLOWED_HOSTS
                if h not in {"*", "localhost", "127.0.0.1"}
            ]
            self.stdout.write(
                f"✅ CSRF_TRUSTED_ORIGINS configurado para producción: {settings.CSRF_TRUSTED_ORIGINS}"
            )

        # Verificar que se aplicó
        self.stdout.write(f"🔍 CSRF_TRUSTED_ORIGINS después: {settings.CSRF_TRUSTED_ORIGINS}")

        self.stdout.write("✅ Configuración aplicada. Ahora puedes probar el login.")
