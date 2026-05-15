from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Busca usuarios por email (búsqueda flexible)"

    def add_arguments(self, parser):
        parser.add_argument(
            "email",
            type=str,
            help="Email o parte del email a buscar",
        )

    def handle(self, *args, **options):
        email_search = options["email"].lower().strip()
        User = get_user_model()

        # Buscar usuarios que contengan el texto en el email
        users = User.objects.filter(email__icontains=email_search)

        if users.exists():
            self.stdout.write(self.style.SUCCESS(f"✅ Encontrados {users.count()} usuario(s):\n"))
            for user in users:
                self.stdout.write(f"  👤 Username: {user.username}")
                self.stdout.write(f"  📧 Email: {user.email}")
                self.stdout.write(f"  ✅ Activo: {user.is_active}")
                self.stdout.write(f"  📅 Fecha registro: {user.date_joined}")

                # Verificar empresa
                try:
                    empresa = user.empresa
                    self.stdout.write(f"  🏢 Empresa: {empresa.nombre_taller}")
                    self.stdout.write(f"  🌍 País: {empresa.pais}")
                    self.stdout.write(f"  💰 Suscripción activa: {empresa.suscripcion_activa}")
                except:
                    self.stdout.write(f"  ⚠️  No tiene empresa asociada")

                self.stdout.write("")
        else:
            self.stdout.write(
                self.style.ERROR(
                    f"❌ No se encontraron usuarios con email que contenga: {email_search}"
                )
            )

            # Buscar también en username
            users_username = User.objects.filter(username__icontains=email_search)
            if users_username.exists():
                self.stdout.write(
                    self.style.WARNING(
                        f"\n💡 Pero encontré {users_username.count()} usuario(s) con ese texto en username:\n"
                    )
                )
                for user in users_username:
                    self.stdout.write(f"  👤 Username: {user.username}")
                    self.stdout.write(f"  📧 Email: {user.email}")
                    self.stdout.write("")
