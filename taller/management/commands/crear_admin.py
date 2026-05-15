"""
Management command para crear o actualizar usuario administrador
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = "Crea o actualiza el usuario administrador con credenciales por defecto."

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            type=str,
            default="admin",
            help="Nombre de usuario (default: admin)",
        )
        parser.add_argument(
            "--password",
            type=str,
            default="admin123",
            help="Contraseña (default: admin123)",
        )
        parser.add_argument(
            "--email",
            type=str,
            default="admin@egarage.com",
            help="Email (default: admin@egarage.com)",
        )

    def handle(self, *args, **options):
        username = options["username"]
        password = options["password"]
        email = options["email"]

        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS("👑 CREANDO/ACTUALIZANDO USUARIO ADMINISTRADOR"))
        self.stdout.write("=" * 80)

        # Crear o obtener usuario
        self.stdout.write(f"\n1️⃣ Creando/actualizando usuario '{username}'...")
        try:
            user = User.objects.get(username=username)
            self.stdout.write(self.style.WARNING(f"   ✅ Usuario '{username}' ya existe"))
            # Actualizar contraseña
            user.set_password(password)
            user.is_staff = True
            user.is_superuser = True
            user.is_active = True
            if email:
                user.email = email
            user.save()
            self.stdout.write(self.style.SUCCESS(f"   ✅ Contraseña actualizada"))
            self.stdout.write(self.style.SUCCESS(f"   ✅ Permisos de administrador activados"))
        except User.DoesNotExist:
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                first_name="Administrador",
                last_name="Sistema",
            )
            self.stdout.write(self.style.SUCCESS(f"   ✅ Usuario '{username}' creado exitosamente"))

        # Resumen final
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(
            self.style.SUCCESS("✅ USUARIO ADMINISTRADOR CREADO/ACTUALIZADO EXITOSAMENTE")
        )
        self.stdout.write("=" * 80)
        self.stdout.write(f"\n📋 CREDENCIALES DE ACCESO:")
        self.stdout.write(f"   Usuario: {username}")
        self.stdout.write(f"   Contraseña: {password}")
        self.stdout.write(f"   Email: {email}")
        self.stdout.write(f"   Staff: {'✅ Sí' if user.is_staff else '❌ No'}")
        self.stdout.write(f"   Superuser: {'✅ Sí' if user.is_superuser else '❌ No'}")
        self.stdout.write(f"   Activo: {'✅ Sí' if user.is_active else '❌ No'}")
        self.stdout.write(f"\n🌐 URL DE ACCESO:")
        self.stdout.write(f"   Admin Django: http://127.0.0.1:8000/admin/")
        self.stdout.write("=" * 80)
