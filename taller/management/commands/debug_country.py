"""
Comando de management para debuggear país y empresa de usuarios.
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from taller.models import Empresa


class Command(BaseCommand):
    help = "Imprime empresa y país de un usuario"

    def add_arguments(self, parser):
        parser.add_argument(
            "--username", required=True, help="Nombre de usuario a verificar"
        )

    def handle(self, *args, **opts):
        User = get_user_model()

        try:
            user = User.objects.get(username=opts["username"])
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"Usuario '{opts['username']}' no existe")
            )
            return

        try:
            empresa = user.empresa
        except Empresa.DoesNotExist:
            empresa = None
        except AttributeError:
            # Si no tiene relación empresa
            try:
                empresa = Empresa.objects.filter(user=user).first()
            except:
                empresa = None

        self.stdout.write(f"🔍 DEBUG USUARIO: {user.username}")
        self.stdout.write(f"📧 Email: {user.email}")
        self.stdout.write(
            f"🏢 Empresa: {getattr(empresa, 'nombre_taller', 'None')} (id={getattr(empresa, 'id', 'None')})"
        )
        self.stdout.write(f"🌍 País: {getattr(empresa, 'pais', 'None')}")

        if empresa:
            self.stdout.write(
                self.style.SUCCESS("✅ Usuario tiene empresa configurada")
            )
            if empresa.pais in ["US", "CL"]:
                self.stdout.write(self.style.SUCCESS(f"✅ País válido: {empresa.pais}"))
            else:
                self.stdout.write(
                    self.style.WARNING(f"⚠️  País no estándar: {empresa.pais}")
                )
        else:
            self.stdout.write(self.style.ERROR("❌ Usuario SIN empresa configurada"))

        # Verificar si hay múltiples empresas
        all_empresas = Empresa.objects.filter(user=user)
        if all_empresas.count() > 1:
            self.stdout.write(
                self.style.WARNING(f"⚠️  Usuario tiene {all_empresas.count()} empresas:")
            )
            for emp in all_empresas:
                self.stdout.write(f"   - {emp.nombre_taller} ({emp.pais})")
