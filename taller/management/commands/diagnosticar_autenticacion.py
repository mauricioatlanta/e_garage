"""
Comando para diagnosticar problemas de autenticación.
Ejecutar: python manage.py diagnosticar_autenticacion --usuario testuser_usa
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model, authenticate
from django.db import transaction
from datetime import datetime, timedelta

User = get_user_model()


class Command(BaseCommand):
    help = "Diagnostica problemas de autenticación para un usuario específico"

    def add_arguments(self, parser):
        parser.add_argument(
            "--usuario",
            type=str,
            required=True,
            help="Username del usuario a diagnosticar",
        )
        parser.add_argument(
            "--password",
            type=str,
            help="Contraseña a probar (si no se proporciona, se usa la conocida)",
        )
        parser.add_argument(
            "--fix",
            action="store_true",
            help="Intentar corregir el problema automáticamente",
        )

    def handle(self, *args, **options):
        username = options["usuario"]
        password_provided = options.get("password")
        fix = options.get("fix", False)

        # Contraseñas conocidas para usuarios de prueba
        passwords_conocidas = {
            "testuser_usa": "TestUSA2025!",
            "test_usa": "test1234",
            "test_usa_pago": "test1234",
            "test_chile": "test1234",
            "test_chile_pago": "test1234",
            "testuser_cl": "test123",
            "admin_chile": "admin123",
            "admin_usa": "admin123",
            "admin": "admin123",
        }

        password = password_provided or passwords_conocidas.get(username, "test1234")

        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS(f"🔍 DIAGNÓSTICO DE AUTENTICACIÓN: {username}"))
        self.stdout.write("=" * 80)
        self.stdout.write("")

        # 1. Verificar si el usuario existe
        try:
            user = User.objects.get(username=username)
            self.stdout.write(self.style.SUCCESS(f"✅ Usuario '{username}' encontrado"))
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"❌ Usuario '{username}' NO EXISTE"))
            self.stdout.write("")

            # Buscar usuarios similares
            usuarios_similares = User.objects.filter(username__icontains=username[:5])
            if usuarios_similares.exists():
                self.stdout.write(self.style.WARNING("📋 Usuarios similares encontrados:"))
                for u in usuarios_similares:
                    self.stdout.write(f"   - {u.username} ({u.email or 'Sin email'})")

            if fix:
                self.stdout.write("")
                self.stdout.write("🔧 Creando usuario...")
                self.crear_usuario_completo(username, password)
            return

        # 2. Información básica del usuario
        self.stdout.write(f"   Email: {user.email or 'Sin email'}")
        self.stdout.write(f"   Activo: {'✅ Sí' if user.is_active else '❌ No'}")
        self.stdout.write(f"   Staff: {'✅ Sí' if user.is_staff else '❌ No'}")
        self.stdout.write(f"   Superuser: {'✅ Sí' if user.is_superuser else '❌ No'}")
        self.stdout.write(f"   Último login: {user.last_login or 'Nunca'}")
        self.stdout.write(f"   Fecha registro: {user.date_joined}")
        self.stdout.write("")

        # 3. Verificar contraseña
        self.stdout.write("🔑 Verificación de Contraseña:")
        password_correcta = user.check_password(password)
        self.stdout.write(f"   Contraseña probada: {password}")
        self.stdout.write(f"   Estado: {'✅ CORRECTA' if password_correcta else '❌ INCORRECTA'}")

        if not password_correcta:
            self.stdout.write(self.style.WARNING("   ⚠️  La contraseña no es correcta"))

            # Intentar otras contraseñas conocidas
            if username in passwords_conocidas:
                for pwd_name, pwd_value in passwords_conocidas.items():
                    if pwd_name == username and pwd_value != password:
                        if user.check_password(pwd_value):
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"   ✅ Encontrada contraseña correcta: {pwd_value}"
                                )
                            )
                            password = pwd_value
                            password_correcta = True
                            break

            # Si aún no funciona y fix está activado, resetear
            if not password_correcta and fix:
                self.stdout.write("")
                self.stdout.write(self.style.WARNING("🔧 Reseteando contraseña..."))
                with transaction.atomic():
                    user.set_password(password)
                    user.save()
                user.refresh_from_db()
                password_correcta = user.check_password(password)
                if password_correcta:
                    self.stdout.write(self.style.SUCCESS(f"✅ Contraseña reseteada a: {password}"))
                else:
                    self.stdout.write(
                        self.style.ERROR("❌ ERROR: No se pudo resetear la contraseña")
                    )

        self.stdout.write("")

        # 4. Verificar autenticación con Django
        self.stdout.write("🔐 Verificación de Autenticación Django:")
        auth_user = authenticate(username=username, password=password)
        if auth_user:
            self.stdout.write(self.style.SUCCESS("   ✅ Autenticación Django: EXITOSA"))
        else:
            self.stdout.write(self.style.ERROR("   ❌ Autenticación Django: FALLIDA"))

            # Diagnóstico del problema
            if not user.is_active:
                self.stdout.write(self.style.ERROR("   Causa: Usuario INACTIVO"))
                if fix:
                    user.is_active = True
                    user.save()
                    self.stdout.write(self.style.SUCCESS("   ✅ Usuario activado"))
            elif not password_correcta:
                self.stdout.write(self.style.ERROR("   Causa: Contraseña INCORRECTA"))
            else:
                self.stdout.write(
                    self.style.ERROR("   Causa: Desconocida (verificar backends de autenticación)")
                )

        self.stdout.write("")

        # 5. Verificar empresa
        self.stdout.write("🏢 Verificación de Empresa:")
        try:
            empresa = user.empresa
            self.stdout.write(self.style.SUCCESS(f"   ✅ Empresa: {empresa.nombre_taller}"))
            self.stdout.write(f"      País: {empresa.pais}")
            self.stdout.write(f"      Moneda: {getattr(empresa, 'moneda', 'N/A')}")
        except AttributeError:
            self.stdout.write(self.style.ERROR("   ❌ Usuario no tiene empresa asociada"))
            if fix:
                self.stdout.write("   🔧 Creando empresa...")
                self.crear_empresa_para_usuario(user)
        self.stdout.write("")

        # 6. Verificar suscripción
        self.stdout.write("📋 Verificación de Suscripción:")
        try:
            suscripcion = user.suscripcion
            self.stdout.write(self.style.SUCCESS(f"   ✅ Suscripción: {suscripcion.tipo}"))
            self.stdout.write(f"      Activa: {'✅ Sí' if suscripcion.activa else '❌ No'}")
            if suscripcion.fecha_fin:
                vencida = suscripcion.fecha_fin < datetime.now().date()
                self.stdout.write(
                    f"      Fecha fin: {suscripcion.fecha_fin} ({'✅ Vigente' if not vencida else '❌ Vencida'})"
                )

            if not suscripcion.activa or (
                suscripcion.fecha_fin and suscripcion.fecha_fin < datetime.now().date()
            ):
                if fix:
                    self.stdout.write("   🔧 Renovando suscripción...")
                    suscripcion.activa = True
                    suscripcion.fecha_fin = (datetime.now() + timedelta(days=30)).date()
                    suscripcion.save()
                    self.stdout.write(self.style.SUCCESS("   ✅ Suscripción renovada"))
        except AttributeError:
            self.stdout.write(self.style.ERROR("   ❌ Usuario no tiene suscripción"))
            if fix:
                self.stdout.write("   🔧 Creando suscripción...")
                self.crear_suscripcion_para_usuario(user)
        self.stdout.write("")

        # 7. Resumen final
        self.stdout.write("=" * 80)
        self.stdout.write("📋 RESUMEN FINAL")
        self.stdout.write("=" * 80)
        self.stdout.write("")

        user.refresh_from_db()

        problemas = []
        if not user.is_active:
            problemas.append("Usuario inactivo")
        if not user.check_password(password):
            problemas.append("Contraseña incorrecta")
        try:
            empresa = user.empresa
        except AttributeError:
            problemas.append("Sin empresa")
        try:
            suscripcion = user.suscripcion
            if not suscripcion.activa:
                problemas.append("Suscripción inactiva")
        except AttributeError:
            problemas.append("Sin suscripción")

        if not problemas:
            self.stdout.write(self.style.SUCCESS("✅ TODO CORRECTO - Usuario listo para usar"))
            self.stdout.write("")
            self.stdout.write(f"🔑 Credenciales:")
            self.stdout.write(f"   Usuario: {username}")
            self.stdout.write(f"   Contraseña: {password}")
            self.stdout.write("")
            self.stdout.write("🌐 URL de acceso:")
            try:
                empresa = user.empresa
                if empresa.pais == "US":
                    self.stdout.write("   https://www.egarage.cl/us/accounts/login/")
                else:
                    self.stdout.write("   https://www.egarage.cl/cl/accounts/login/")
            except:
                self.stdout.write("   https://www.egarage.cl/accounts/login/")
        else:
            self.stdout.write(self.style.ERROR("❌ PROBLEMAS ENCONTRADOS:"))
            for problema in problemas:
                self.stdout.write(f"   - {problema}")

            if not fix:
                self.stdout.write("")
                self.stdout.write("💡 Para intentar corregir automáticamente:")
                self.stdout.write(
                    f"   python manage.py diagnosticar_autenticacion --usuario {username} --fix"
                )

        self.stdout.write("")

    def crear_usuario_completo(self, username, password):
        """Crear usuario completo con empresa y suscripción"""
        from taller.models import Empresa, Suscripcion

        # Determinar país basado en username
        pais = "US" if "usa" in username.lower() else "CL"

        with transaction.atomic():
            user = User.objects.create_user(
                username=username,
                email=f"{username}@egarage.{'com' if pais == 'US' else 'cl'}",
                password=password,
                is_active=True,
            )

            # Crear empresa
            empresa = Empresa.objects.create(
                user=user,
                nombre_taller=f"Taller de {username}",
                pais=pais,
                telefono="+15551234567" if pais == "US" else "+56912345678",
                moneda="USD" if pais == "US" else "CLP",
            )

            # Crear suscripción
            Suscripcion.objects.create(
                user=user,
                tipo="trial",
                activa=True,
                fecha_inicio=datetime.now().date(),
                fecha_fin=(datetime.now() + timedelta(days=30)).date(),
            )

            self.stdout.write(self.style.SUCCESS(f"✅ Usuario creado exitosamente"))
            self.stdout.write(f"   Empresa: {empresa.nombre_taller}")
            self.stdout.write(f"   País: {empresa.pais}")

    def crear_empresa_para_usuario(self, user):
        """Crear empresa para un usuario existente"""
        from taller.models import Empresa

        pais = "US" if "usa" in user.username.lower() else "CL"

        with transaction.atomic():
            empresa = Empresa.objects.create(
                user=user,
                nombre_taller=f"Taller de {user.username}",
                pais=pais,
                telefono="+15551234567" if pais == "US" else "+56912345678",
                moneda="USD" if pais == "US" else "CLP",
            )
            self.stdout.write(self.style.SUCCESS(f"✅ Empresa creada: {empresa.nombre_taller}"))

    def crear_suscripcion_para_usuario(self, user):
        """Crear suscripción para un usuario existente"""
        from taller.models import Suscripcion

        with transaction.atomic():
            suscripcion = Suscripcion.objects.create(
                user=user,
                tipo="trial",
                activa=True,
                fecha_inicio=datetime.now().date(),
                fecha_fin=(datetime.now() + timedelta(days=30)).date(),
            )
            self.stdout.write(
                self.style.SUCCESS(f"✅ Suscripción creada hasta {suscripcion.fecha_fin}")
            )
