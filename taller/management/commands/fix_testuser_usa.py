"""
Comando de Django para verificar y corregir las credenciales de testuser_usa
Ejecutar: python manage.py fix_testuser_usa
"""

from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from taller.models import Empresa, Suscripcion

User = get_user_model()


class Command(BaseCommand):
    help = "Verifica y corrige las credenciales de testuser_usa"

    def handle(self, *args, **options):
        username = "testuser_usa"
        password = "TestUSA2025!"
        email = "testuser@usa-garage.com"

        self.stdout.write("=" * 70)
        self.stdout.write(self.style.SUCCESS("🔍 VERIFICACIÓN Y CORRECCIÓN DE testuser_usa"))
        self.stdout.write("=" * 70)
        self.stdout.write("")

        # 1. Verificar si el usuario existe
        try:
            user = User.objects.get(username=username)
            self.stdout.write(self.style.SUCCESS(f"✅ Usuario '{username}' encontrado"))
            self.stdout.write(f"   Email: {user.email}")
            self.stdout.write(f"   Activo: {user.is_active}")
            self.stdout.write(f"   Staff: {user.is_staff}")
            self.stdout.write(f"   Superuser: {user.is_superuser}")
            self.stdout.write("")
        except User.DoesNotExist:
            self.stdout.write(
                self.style.WARNING(f"❌ Usuario '{username}' NO existe. Creando usuario...")
            )
            with transaction.atomic():
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name="Test",
                    last_name="User USA",
                    is_active=True,
                )
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Usuario '{username}' creado exitosamente")
                )
                self.stdout.write("")

        # 2. Resetear contraseña para asegurar que funcione
        self.stdout.write("🔑 Reseteando contraseña...")
        user.set_password(password)
        user.save()
        self.stdout.write(self.style.SUCCESS(f"✅ Contraseña reseteada a: {password}"))
        self.stdout.write("")

        # 3. Asegurar que el usuario esté activo
        if not user.is_active:
            user.is_active = True
            user.save()
            self.stdout.write(self.style.SUCCESS("✅ Usuario activado"))
            self.stdout.write("")

        # 4. Verificar/Crear empresa
        try:
            empresa = user.empresa
            self.stdout.write(self.style.SUCCESS(f"✅ Empresa encontrada: {empresa.nombre_taller}"))
            self.stdout.write(f"   País: {empresa.pais}")
            self.stdout.write(f"   Moneda: {getattr(empresa, 'moneda', 'USD')}")

            # Asegurar que el país sea US
            if empresa.pais != "US":
                empresa.pais = "US"
                empresa.save()
                self.stdout.write(self.style.SUCCESS(f"✅ País de empresa actualizado a US"))
            self.stdout.write("")
        except AttributeError:
            self.stdout.write(
                self.style.WARNING("❌ Usuario no tiene empresa asociada. Creando empresa...")
            )
            with transaction.atomic():
                empresa = Empresa.objects.create(
                    user=user,
                    nombre_taller="Taller de testuser_usa",
                    pais="US",
                    telefono="+15551234567",
                    direccion="Miami, FL, USA",
                    moneda="USD",
                )
                self.stdout.write(self.style.SUCCESS(f"✅ Empresa creada: {empresa.nombre_taller}"))
                self.stdout.write(f"   País: {empresa.pais}")
                self.stdout.write(f"   Moneda: {getattr(empresa, 'moneda', 'USD')}")
                self.stdout.write("")

        # 5. Verificar/Crear suscripción
        try:
            suscripcion = user.suscripcion
            self.stdout.write(self.style.SUCCESS(f"✅ Suscripción encontrada:"))
            self.stdout.write(f"   Tipo: {suscripcion.tipo}")
            self.stdout.write(f"   Activa: {suscripcion.activa}")
            self.stdout.write(f"   Fecha inicio: {suscripcion.fecha_inicio}")
            self.stdout.write(f"   Fecha fin: {suscripcion.fecha_fin}")

            # Verificar si está vencida
            vencida = False
            if suscripcion.fecha_fin:
                vencida = suscripcion.fecha_fin < datetime.now().date()
                self.stdout.write(f"   Vencida: {vencida}")

            # Si está vencida o inactiva, crear nueva suscripción trial
            if not suscripcion.activa or vencida:
                self.stdout.write(
                    self.style.WARNING(
                        "⚠️ Suscripción vencida o inactiva. Creando nueva suscripción trial..."
                    )
                )
                with transaction.atomic():
                    # Desactivar suscripción anterior
                    suscripcion.activa = False
                    suscripcion.save()

                    # Crear nueva suscripción trial
                    nueva_suscripcion = Suscripcion.objects.create(
                        user=user,
                        tipo="trial",
                        activa=True,
                        fecha_inicio=datetime.now().date(),
                        fecha_fin=(datetime.now() + timedelta(days=30)).date(),
                    )
                    self.stdout.write(self.style.SUCCESS(f"✅ Nueva suscripción trial creada"))
                    self.stdout.write(f"   Fecha inicio: {nueva_suscripcion.fecha_inicio}")
                    self.stdout.write(f"   Fecha fin: {nueva_suscripcion.fecha_fin}")
                    self.stdout.write("")
            else:
                self.stdout.write(self.style.SUCCESS("✅ Suscripción activa y vigente"))
                self.stdout.write("")
        except AttributeError:
            self.stdout.write(
                self.style.WARNING("❌ Usuario no tiene suscripción. Creando suscripción trial...")
            )
            with transaction.atomic():
                suscripcion = Suscripcion.objects.create(
                    user=user,
                    tipo="trial",
                    activa=True,
                    fecha_inicio=datetime.now().date(),
                    fecha_fin=(datetime.now() + timedelta(days=30)).date(),
                )
                self.stdout.write(self.style.SUCCESS(f"✅ Suscripción trial creada"))
                self.stdout.write(f"   Tipo: {suscripcion.tipo}")
                self.stdout.write(f"   Activa: {suscripcion.activa}")
                self.stdout.write(f"   Fecha inicio: {suscripcion.fecha_inicio}")
                self.stdout.write(f"   Fecha fin: {suscripcion.fecha_fin}")
                self.stdout.write("")

        # 6. Verificar que puede autenticarse
        self.stdout.write("🔐 Verificando autenticación...")
        test_user = User.objects.get(username=username)
        if test_user.check_password(password):
            self.stdout.write(
                self.style.SUCCESS("✅ La contraseña es correcta y el usuario puede autenticarse")
            )
        else:
            self.stdout.write(self.style.ERROR("❌ ERROR: La contraseña no coincide"))
        self.stdout.write("")

        # 7. Resumen final
        self.stdout.write("=" * 70)
        self.stdout.write(self.style.SUCCESS("📋 RESUMEN FINAL"))
        self.stdout.write("=" * 70)
        self.stdout.write("")
        self.stdout.write("🔑 CREDENCIALES DE ACCESO:")
        self.stdout.write(f"   Usuario: {username}")
        self.stdout.write(f"   Contraseña: {password}")
        self.stdout.write(f"   Email: {user.email}")
        self.stdout.write("")
        self.stdout.write("🌐 URLS DE ACCESO:")
        self.stdout.write("   Login USA: https://www.egarage.cl/us/accounts/login/")
        self.stdout.write("   Dashboard USA: https://www.egarage.cl/us/")
        self.stdout.write("")

        try:
            empresa = user.empresa
            self.stdout.write("🏢 EMPRESA:")
            self.stdout.write(f"   Nombre: {empresa.nombre_taller}")
            self.stdout.write(f"   País: {empresa.pais}")
            self.stdout.write(f"   Moneda: {getattr(empresa, 'moneda', 'USD')}")
            self.stdout.write("")
        except:
            pass

        try:
            suscripcion = user.suscripcion
            self.stdout.write("📋 SUSCRIPCIÓN:")
            self.stdout.write(f"   Tipo: {suscripcion.tipo}")
            self.stdout.write(f"   Estado: {'Activa' if suscripcion.activa else 'Inactiva'}")
            if suscripcion.fecha_fin:
                self.stdout.write(f"   Válida hasta: {suscripcion.fecha_fin}")
            self.stdout.write("")
        except:
            pass

        self.stdout.write(self.style.SUCCESS("✅ USUARIO LISTO PARA USAR"))
        self.stdout.write("=" * 70)
