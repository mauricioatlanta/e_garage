from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from taller.documentos.models import Documento


class Command(BaseCommand):
    help = "Cambiar la contraseña del usuario test_diagnostic para acceder al documento 45"

    def handle(self, *args, **options):
        username = "test_diagnostic"
        new_password = "test123"

        try:
            user = User.objects.get(username=username)
            user.set_password(new_password)
            user.save()

            self.stdout.write(self.style.SUCCESS(f"✓ Contraseña cambiada para {username}"))
            self.stdout.write(f"Nueva contraseña: {new_password}")
            self.stdout.write(f"Empresa: {user.empresa.nombre_taller}")

            # Verificar documentos disponibles
            docs = Documento.objects.filter(empresa=user.empresa)
            self.stdout.write(f"Documentos disponibles: {docs.count()}")

            if docs.exists():
                for doc in docs[:5]:
                    self.stdout.write(f"- Documento {doc.id}: {doc.tipo} ({doc.estado})")

            self.stdout.write("\nPara acceder al documento 45:")
            self.stdout.write("1. Ve a http://127.0.0.1:8000/us/accounts/login/")
            self.stdout.write(f"2. Inicia sesión con: {username} / {new_password}")
            self.stdout.write("3. Ve a http://127.0.0.1:8000/us/documentos/form/45/")

        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Usuario {username} no existe"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
