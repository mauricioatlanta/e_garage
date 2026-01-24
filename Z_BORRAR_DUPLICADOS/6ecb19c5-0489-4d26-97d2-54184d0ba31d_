from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from taller.models import Empresa


class Command(BaseCommand):
    help = "Corrige el país de la empresa del usuario testuser_usa a US"

    def handle(self, *args, **options):
        try:
            user = User.objects.get(username="testuser_usa")
            self.stdout.write(f"✓ Usuario encontrado: {user.username}")

            try:
                empresa = Empresa.objects.get(user=user)
                self.stdout.write(f"✓ Empresa encontrada: {empresa.nombre_taller}")
                self.stdout.write(f"  País actual: {empresa.pais}")

                if empresa.pais != "US":
                    empresa.pais = "US"
                    empresa.save()
                    self.stdout.write(self.style.SUCCESS(f"✅ País actualizado a: {empresa.pais}"))
                else:
                    self.stdout.write(
                        self.style.SUCCESS("✅ El país ya está configurado correctamente como US")
                    )

            except Empresa.DoesNotExist:
                self.stdout.write("❌ No se encontró empresa, creando una nueva...")
                empresa = Empresa.objects.create(
                    user=user, nombre_taller="USA Test Garage", pais="US"
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ Empresa creada: {empresa.nombre_taller} (País: {empresa.pais})"
                    )
                )

            # Verificar resultado
            empresa.refresh_from_db()
            self.stdout.write("\n📋 Estado final:")
            self.stdout.write(f"  - Usuario: {user.username}")
            self.stdout.write(f"  - Empresa: {empresa.nombre_taller}")
            self.stdout.write(f"  - País: {empresa.pais}")

            if empresa.pais == "US":
                self.stdout.write(
                    self.style.SUCCESS(
                        "🇺🇸 ¡Corrección completada! El usuario ahora debería ver la bandera de USA."
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR("❌ Algo salió mal, el país no se actualizó correctamente.")
                )

        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR("❌ Usuario testuser_usa no existe"))
