"""
Comando Django para listar todos los usuarios y sus credenciales.
Ejecutar: python manage.py listar_usuarios_credenciales
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.db import transaction

User = get_user_model()


class Command(BaseCommand):
    help = "Lista todos los usuarios del sistema con información de credenciales y empresas"

    def add_arguments(self, parser):
        parser.add_argument(
            "--usuario",
            type=str,
            help="Buscar usuario específico por username",
        )
        parser.add_argument(
            "--pais",
            type=str,
            help="Filtrar por país (CL, US, etc.)",
        )
        parser.add_argument(
            "--reset-testuser-usa",
            action="store_true",
            help="Resetear contraseña de testuser_usa a TestUSA2025!",
        )

    def handle(self, *args, **options):
        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS("🔍 LISTADO DE USUARIOS Y CREDENCIALES"))
        self.stdout.write("=" * 80)
        self.stdout.write("")

        # Filtrar por usuario específico si se proporciona
        username_filter = options.get("usuario")
        pais_filter = options.get("pais")

        # Resetear testuser_usa si se solicita
        if options.get("reset_testuser_usa"):
            self.resetear_testuser_usa()
            return

        # Obtener todos los usuarios
        if username_filter:
            usuarios = User.objects.filter(username__icontains=username_filter)
            self.stdout.write(
                self.style.WARNING(f"🔍 Buscando usuarios que contengan: {username_filter}")
            )
        else:
            usuarios = User.objects.all().order_by("username")

        self.stdout.write(f"📊 Total de usuarios encontrados: {usuarios.count()}")
        self.stdout.write("")

        # Agrupar por país
        usuarios_por_pais = {}
        usuarios_sin_empresa = []

        for user in usuarios:
            try:
                empresa = user.empresa
                pais = getattr(empresa, "pais", "N/A")

                # Filtrar por país si se especifica
                if pais_filter and pais.upper() != pais_filter.upper():
                    continue

                if pais not in usuarios_por_pais:
                    usuarios_por_pais[pais] = []
                usuarios_por_pais[pais].append((user, empresa))
            except AttributeError:
                usuarios_sin_empresa.append(user)

        # Mostrar usuarios por país
        for pais in sorted(usuarios_por_pais.keys()):
            usuarios_pais = usuarios_por_pais[pais]
            self.stdout.write("")
            self.stdout.write(self.style.SUCCESS(f"🌍 {pais} ({len(usuarios_pais)} usuarios)"))
            self.stdout.write("-" * 80)

            for user, empresa in usuarios_pais:
                self.mostrar_usuario(user, empresa)

        # Mostrar usuarios sin empresa
        if usuarios_sin_empresa:
            self.stdout.write("")
            self.stdout.write(
                self.style.WARNING(f"⚠️  Usuarios sin empresa ({len(usuarios_sin_empresa)})")
            )
            self.stdout.write("-" * 80)
            for user in usuarios_sin_empresa:
                self.mostrar_usuario(user, None)

        # Mostrar usuarios de prueba conocidos
        self.stdout.write("")
        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS("🔑 USUARIOS DE PRUEBA CONOCIDOS"))
        self.stdout.write("=" * 80)
        self.stdout.write("")

        usuarios_prueba = [
            "testuser_usa",
            "test_usa",
            "test_usa_pago",
            "test_chile",
            "test_chile_pago",
            "testuser_cl",
            "admin_chile",
            "admin_usa",
            "admin",
        ]

        for username_prueba in usuarios_prueba:
            try:
                user = User.objects.get(username=username_prueba)
                self.mostrar_usuario_detallado(user)
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"❌ {username_prueba} - NO EXISTE"))

        self.stdout.write("")
        self.stdout.write("=" * 80)

    def mostrar_usuario(self, user, empresa):
        """Mostrar información básica de un usuario"""
        estado = "✅ Activo" if user.is_active else "❌ Inactivo"
        tipo = (
            "👑 Superuser" if user.is_superuser else ("🔧 Staff" if user.is_staff else "👤 Normal")
        )

        self.stdout.write(f"{tipo} {user.username}")
        self.stdout.write(f"   Email: {user.email or 'Sin email'}")
        self.stdout.write(f"   Estado: {estado}")

        if empresa:
            self.stdout.write(f"   Empresa: {empresa.nombre_taller}")
            self.stdout.write(f"   País: {empresa.pais}")

            # Verificar suscripción
            try:
                suscripcion = user.suscripcion
                estado_suscripcion = "✅ Activa" if suscripcion.activa else "❌ Inactiva"
                self.stdout.write(f"   Suscripción: {suscripcion.tipo} - {estado_suscripcion}")
                if suscripcion.fecha_fin:
                    self.stdout.write(f"   Válida hasta: {suscripcion.fecha_fin}")
            except AttributeError:
                self.stdout.write(self.style.WARNING("   Suscripción: No tiene"))

        self.stdout.write("")

    def mostrar_usuario_detallado(self, user):
        """Mostrar información detallada de un usuario"""
        self.stdout.write(self.style.SUCCESS(f"\n📋 {user.username}"))
        self.stdout.write(f"   Email: {user.email or 'Sin email'}")
        self.stdout.write(f"   Activo: {'✅ Sí' if user.is_active else '❌ No'}")
        self.stdout.write(f"   Staff: {'✅ Sí' if user.is_staff else '❌ No'}")
        self.stdout.write(f"   Superuser: {'✅ Sí' if user.is_superuser else '❌ No'}")
        self.stdout.write(f"   Último login: {user.last_login or 'Nunca'}")
        self.stdout.write(f"   Fecha registro: {user.date_joined}")

        # Verificar empresa
        try:
            empresa = user.empresa
            self.stdout.write(self.style.SUCCESS(f"   ✅ Empresa: {empresa.nombre_taller}"))
            self.stdout.write(f"      País: {empresa.pais}")
            self.stdout.write(f"      Moneda: {getattr(empresa, 'moneda', 'N/A')}")
        except AttributeError:
            self.stdout.write(self.style.WARNING("   ❌ Sin empresa"))

        # Verificar suscripción
        try:
            suscripcion = user.suscripcion
            self.stdout.write(self.style.SUCCESS(f"   ✅ Suscripción: {suscripcion.tipo}"))
            self.stdout.write(f"      Activa: {'✅ Sí' if suscripcion.activa else '❌ No'}")
            if suscripcion.fecha_fin:
                vencida = suscripcion.fecha_fin < self.get_current_date()
                self.stdout.write(
                    f"      Fecha fin: {suscripcion.fecha_fin} ({'✅ Vigente' if not vencida else '❌ Vencida'})"
                )
        except AttributeError:
            self.stdout.write(self.style.WARNING("   ❌ Sin suscripción"))

    def get_current_date(self):
        """Obtener fecha actual"""
        from datetime import date

        return date.today()

    def resetear_testuser_usa(self):
        """Resetear contraseña de testuser_usa"""
        self.stdout.write("")
        self.stdout.write(self.style.WARNING("🔧 RESETEANDO CONTRASEÑA DE testuser_usa..."))
        self.stdout.write("")

        username = "testuser_usa"
        password = "TestUSA2025!"

        try:
            user = User.objects.get(username=username)
            self.stdout.write(self.style.SUCCESS(f"✅ Usuario '{username}' encontrado"))

            # Resetear contraseña
            with transaction.atomic():
                user.set_password(password)
                user.is_active = True
                user.save()

            self.stdout.write(self.style.SUCCESS(f"✅ Contraseña reseteada a: {password}"))
            self.stdout.write(self.style.SUCCESS(f"✅ Usuario activado: {user.is_active}"))

            # Verificar que funciona
            test_user = User.objects.get(username=username)
            if test_user.check_password(password):
                self.stdout.write(self.style.SUCCESS("✅ Verificación: Contraseña correcta"))
            else:
                self.stdout.write(self.style.ERROR("❌ ERROR: Contraseña no coincide"))

        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"❌ Usuario '{username}' NO existe"))
            self.stdout.write("   Ejecutar: python manage.py fix_testuser_usa")
