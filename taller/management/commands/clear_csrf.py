"""
Comando para limpiar tokens CSRF y sesiones.
Útil cuando hay problemas de CSRF en desarrollo.
"""

from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.core.management.base import BaseCommand
from django.db import connection

User = get_user_model()


class Command(BaseCommand):
    help = "Limpia tokens CSRF y sesiones para resolver problemas de autenticación"

    def add_arguments(self, parser):
        parser.add_argument(
            "--sessions-only",
            action="store_true",
            help="Solo limpiar sesiones, mantener tokens CSRF",
        )
        parser.add_argument(
            "--csrf-only",
            action="store_true",
            help="Solo limpiar tokens CSRF, mantener sesiones",
        )

    def handle(self, *args, **options):
        sessions_only = options["sessions_only"]
        csrf_only = options["csrf_only"]

        if not sessions_only:
            # Limpiar tokens CSRF de la base de datos
            self.stdout.write("Limpiando tokens CSRF...")
            with connection.cursor() as cursor:
                # Limpiar tabla de sesiones que puede contener tokens CSRF
                cursor.execute(
                    "DELETE FROM django_session WHERE session_data LIKE '%csrf%'"
                )
                csrf_deleted = cursor.rowcount
                self.stdout.write(f"  - Tokens CSRF eliminados: {csrf_deleted}")

        if not csrf_only:
            # Limpiar todas las sesiones
            self.stdout.write("Limpiando sesiones...")
            sessions_deleted = Session.objects.all().count()
            Session.objects.all().delete()
            self.stdout.write(f"  - Sesiones eliminadas: {sessions_deleted}")

        self.stdout.write(
            self.style.SUCCESS(
                "✅ Limpieza completada. Los usuarios necesitarán hacer login nuevamente."
            )
        )
        self.stdout.write(
            self.style.WARNING(
                "💡 Si el problema persiste, limpie las cookies del navegador manualmente."
            )
        )
