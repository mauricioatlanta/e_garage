from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from taller.models.empresa import Empresa
from taller.models.suscripcion import Suscripcion
from taller.utils.pais_utils import get_configuracion_pais


class Command(BaseCommand):
    help = "Activa una cuenta de usuario para USA y asegura que tenga suscripción activa."

    def add_arguments(self, parser):
        parser.add_argument(
            "email",
            type=str,
            help="Email del usuario a activar",
        )

    def handle(self, *args, **options):
        email = options["email"].lower().strip()
        User = get_user_model()

        try:
            # Buscar usuario por email
            user = User.objects.filter(email__iexact=email).first()

            if not user:
                self.stdout.write(
                    self.style.WARNING(f"⚠️  Usuario con email {email} no encontrado.")
                )
                self.stdout.write(
                    self.style.WARNING("💡 Creando nuevo usuario y activando suscripción...")
                )

                # Crear usuario con username = email
                username = email.lower().strip()
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password="TempPassword123!",  # Contraseña temporal que debe cambiar
                    first_name="Angels",
                    last_name="Automotive",
                    is_active=True,
                )
                self.stdout.write(self.style.SUCCESS(f"✅ Usuario creado: {user.username}"))
                self.stdout.write(
                    self.style.WARNING(
                        f"🔑 Contraseña temporal: TempPassword123! (debe cambiarla al iniciar sesión)"
                    )
                )

            self.stdout.write(self.style.SUCCESS(f"✅ Usuario encontrado: {user.username}"))

            # Activar usuario
            if not user.is_active:
                user.is_active = True
                user.save()
                self.stdout.write(self.style.SUCCESS("✅ Usuario activado (is_active=True)"))

            # Verificar y activar email en EmailAddress (allauth)
            try:
                from allauth.account.models import EmailAddress

                email_address, created = EmailAddress.objects.get_or_create(
                    user=user,
                    email=email,
                    defaults={"verified": True, "primary": True},
                )

                if not email_address.verified:
                    email_address.verified = True
                    email_address.primary = True
                    email_address.save()
                    self.stdout.write(self.style.SUCCESS("✅ Email verificado en EmailAddress"))
                else:
                    self.stdout.write(self.style.SUCCESS("✅ Email ya estaba verificado"))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"⚠️  Error al verificar email: {e}"))

            # Asegurar que tenga Empresa para USA
            empresa, created = Empresa.objects.get_or_create(
                user=user,
                defaults={
                    "nombre_taller": f"Taller de {user.first_name or user.username}",
                    "email": email,
                    "pais": "US",
                    "plan": "trial",
                    "dias_prueba": 30,
                    "suscripcion_activa": True,
                    "fecha_inicio": timezone.now(),
                    "fecha_fin": timezone.now() + timedelta(days=30),
                },
            )

            # Configurar país y moneda si no está configurado para USA
            if empresa.pais != "US":
                empresa.pais = "US"
                self.stdout.write(self.style.WARNING("⚠️  País cambiado a US"))

            # Obtener configuración del país
            pais_config = get_configuracion_pais(empresa)

            empresa.moneda = pais_config["moneda"]
            empresa.zona_horaria = pais_config["zona_horaria_default"]

            # Activar suscripción si no está activa
            if not empresa.suscripcion_activa:
                empresa.suscripcion_activa = True
                self.stdout.write(self.style.SUCCESS("✅ Suscripción de empresa activada"))

            # Extender fecha de fin si está vencida o cerca de vencer
            if not empresa.fecha_fin or empresa.fecha_fin <= timezone.now():
                empresa.fecha_fin = timezone.now() + timedelta(days=30)
                empresa.fecha_inicio = timezone.now()
                self.stdout.write(self.style.SUCCESS("✅ Fecha de suscripción extendida 30 días"))

            empresa.save()

            if created:
                self.stdout.write(self.style.SUCCESS(f"✅ Empresa creada: {empresa.nombre_taller}"))
            else:
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Empresa actualizada: {empresa.nombre_taller}")
                )

            # Asegurar que tenga Suscripcion (modelo antiguo si existe)
            try:
                suscripcion, created = Suscripcion.objects.get_or_create(
                    user=user,
                    defaults={
                        "tipo": "trial",
                        "activa": True,
                        "fecha_inicio": timezone.now().date(),
                        "fecha_fin": timezone.now().date() + timedelta(days=30),
                    },
                )

                if not suscripcion.activa:
                    suscripcion.activar()
                    self.stdout.write(
                        self.style.SUCCESS("✅ Suscripción (modelo antiguo) activada")
                    )
                elif suscripcion.esta_vencida():
                    suscripcion.activar()
                    self.stdout.write(
                        self.style.SUCCESS("✅ Suscripción (modelo antiguo) reactivada")
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS("✅ Suscripción (modelo antiguo) ya está activa")
                    )
            except Exception as e:
                # El modelo Suscripcion puede no existir, no es crítico
                self.stdout.write(
                    self.style.WARNING(f"⚠️  Info: Modelo Suscripcion no disponible: {e}")
                )

            # Resumen final
            self.stdout.write(self.style.SUCCESS("\n" + "=" * 60))
            self.stdout.write(self.style.SUCCESS("✅ CUENTA ACTIVADA EXITOSAMENTE"))
            self.stdout.write(self.style.SUCCESS("=" * 60))
            self.stdout.write(f"👤 Usuario: {user.username}")
            self.stdout.write(f"📧 Email: {user.email}")
            self.stdout.write(f"🏢 Empresa: {empresa.nombre_taller}")
            self.stdout.write(f"🌍 País: {empresa.pais}")
            self.stdout.write(f"💰 Moneda: {empresa.moneda}")
            self.stdout.write(f"📅 Suscripción activa: {empresa.suscripcion_activa}")
            self.stdout.write(
                f"📆 Fecha fin: {empresa.fecha_fin.strftime('%Y-%m-%d') if empresa.fecha_fin else 'N/A'}"
            )
            self.stdout.write(f"🌐 URL Login USA: /us/accounts/login/")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error: {str(e)}"))
            import traceback

            traceback.print_exc()
