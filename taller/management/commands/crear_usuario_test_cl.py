"""
Management command para crear o actualizar usuario test_cl para Chile
Incluye: Usuario, Empresa y Suscripción activa
"""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from taller.models.empresa import Empresa
from taller.models.suscripcion import Suscripcion

User = get_user_model()


class Command(BaseCommand):
    help = "Crea o actualiza el usuario test_cl para Chile con empresa y suscripción activa."

    def handle(self, *args, **options):
        username = "test_cl"
        password = "Egarage123!"
        email = "test_cl@egarage.cl"

        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS("🇨🇱 CREANDO/ACTUALIZANDO USUARIO test_cl PARA CHILE"))
        self.stdout.write("=" * 80)

        # Paso 1: Crear o obtener usuario
        self.stdout.write("\n1️⃣ Creando/actualizando usuario...")
        try:
            user = User.objects.get(username=username)
            self.stdout.write(self.style.WARNING(f"   ✅ Usuario '{username}' ya existe"))
            # Actualizar contraseña
            user.set_password(password)
            self.stdout.write(self.style.SUCCESS(f"   ✅ Contraseña actualizada"))
        except User.DoesNotExist:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name="Test",
                last_name="Chile",
                is_active=True,
                is_staff=False,
                is_superuser=False,
            )
            self.stdout.write(self.style.SUCCESS(f"   ✅ Usuario '{username}' creado exitosamente"))

        # Verificar que el usuario está activo
        if not user.is_active:
            user.is_active = True
            user.save()
            self.stdout.write(self.style.SUCCESS(f"   ✅ Usuario '{username}' activado"))

        # Verificar contraseña
        if not user.check_password(password):
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"   ✅ Contraseña verificada y actualizada"))

        # Paso 2: Crear o obtener empresa
        self.stdout.write("\n2️⃣ Creando/actualizando empresa...")
        try:
            empresa = Empresa.objects.get(user=user)
            self.stdout.write(
                self.style.WARNING(f"   ✅ Empresa '{empresa.nombre_taller}' ya existe")
            )
            # Actualizar país si no es CL
            if empresa.pais != "CL":
                empresa.pais = "CL"
                empresa.save()
                self.stdout.write(self.style.SUCCESS(f"   ✅ País actualizado a CL"))
        except Empresa.DoesNotExist:
            empresa = Empresa.objects.create(
                user=user,
                nombre_taller="Taller de test_cl",
                empresa="eGarage Chile Test",
                direccion="Av. Providencia 123, Santiago, Chile",
                telefono="+56912345678",
                email=email,
                pais="CL",  # Importante: país Chile
                zona_horaria="America/Santiago",
            )
            self.stdout.write(
                self.style.SUCCESS(f"   ✅ Empresa '{empresa.nombre_taller}' creada exitosamente")
            )

        # Paso 3: Crear o actualizar suscripción
        self.stdout.write("\n3️⃣ Creando/actualizando suscripción...")
        try:
            suscripcion = Suscripcion.objects.get(user=user)
            self.stdout.write(
                self.style.WARNING(f"   ✅ Suscripción ya existe (tipo: {suscripcion.tipo})")
            )

            # Actualizar suscripción para asegurar que esté activa y vigente
            fecha_inicio = timezone.now().date()
            fecha_fin = fecha_inicio + timedelta(days=30)  # 30 días de prueba

            suscripcion.tipo = "trial"
            suscripcion.fecha_inicio = fecha_inicio
            suscripcion.fecha_fin = fecha_fin
            suscripcion.activa = True
            suscripcion.save()

            self.stdout.write(self.style.SUCCESS(f"   ✅ Suscripción actualizada:"))
            self.stdout.write(f"      - Tipo: {suscripcion.tipo}")
            self.stdout.write(f"      - Estado: {'Activa' if suscripcion.activa else 'Inactiva'}")
            self.stdout.write(f"      - Fecha inicio: {suscripcion.fecha_inicio}")
            self.stdout.write(f"      - Fecha fin: {suscripcion.fecha_fin}")
            self.stdout.write(
                f"      - Vigente: {'Sí' if not suscripcion.esta_vencida() else 'No'}"
            )

        except Suscripcion.DoesNotExist:
            # Crear nueva suscripción
            fecha_inicio = timezone.now().date()
            fecha_fin = fecha_inicio + timedelta(days=30)  # 30 días de prueba

            suscripcion = Suscripcion.objects.create(
                user=user,
                tipo="trial",
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                activa=True,
            )

            self.stdout.write(self.style.SUCCESS(f"   ✅ Suscripción creada exitosamente:"))
            self.stdout.write(f"      - Tipo: {suscripcion.tipo}")
            self.stdout.write(f"      - Estado: Activa")
            self.stdout.write(f"      - Fecha inicio: {suscripcion.fecha_inicio}")
            self.stdout.write(f"      - Fecha fin: {suscripcion.fecha_fin}")
            self.stdout.write(
                f"      - Vigente: {'Sí' if not suscripcion.esta_vencida() else 'No'}"
            )

        # Resumen final
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(self.style.SUCCESS("✅ USUARIO test_cl CREADO/ACTUALIZADO EXITOSAMENTE"))
        self.stdout.write("=" * 80)
        self.stdout.write(f"\n📋 CREDENCIALES DE ACCESO:")
        self.stdout.write(f"   Usuario: {username}")
        self.stdout.write(f"   Contraseña: {password}")
        self.stdout.write(f"   Email: {email}")
        self.stdout.write(f"\n🏢 EMPRESA:")
        self.stdout.write(f"   Nombre: {empresa.nombre_taller}")
        self.stdout.write(f"   País: {empresa.pais}")
        self.stdout.write(f"\n📅 SUSCRIPCIÓN:")
        self.stdout.write(f"   Tipo: {suscripcion.tipo}")
        self.stdout.write(f"   Estado: {'Activa' if suscripcion.activa else 'Inactiva'}")
        self.stdout.write(f"   Vigente: {'Sí' if not suscripcion.esta_vencida() else 'No'}")
        self.stdout.write(f"   Vence: {suscripcion.fecha_fin}")
        self.stdout.write(f"\n🌐 URLs DE ACCESO:")
        self.stdout.write(f"   Login Chile: http://127.0.0.1:8000/cl/accounts/login/")
        self.stdout.write(f"   Dashboard Chile: http://127.0.0.1:8000/cl/")
        self.stdout.write(f"   Login Servidor: https://www.egarage.cl/cl/accounts/login/")
        self.stdout.write("=" * 80)
