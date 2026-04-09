from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from allauth.account.models import EmailAddress

from taller.models.empresa import Empresa
from taller.models.suscripcion import Suscripcion
from taller.utils.country_config import get_country_config


@dataclass(frozen=True)
class DemoAccountSpec:
    username: str
    email: str
    password: str
    country: str
    company_name: str


DEMO_ACCOUNTS = (
    DemoAccountSpec(
        username="test_cl",
        email="test_cl@egarage.cl",
        password="Egarage123!",
        country="CL",
        company_name="Taller de test_cl",
    ),
    DemoAccountSpec(
        username="testuser_usa",
        email="testuser@usa-garage.com",
        password="TestUSA2025!",
        country="US",
        company_name="Taller de testuser_usa",
    ),
    DemoAccountSpec(
        username="demo_ar",
        email="demo_ar@egarage.cl",
        password="DemoAR123!",
        country="AR",
        company_name="eGarage Demo Argentina",
    ),
    DemoAccountSpec(
        username="demo_br",
        email="demo_br@egarage.cl",
        password="DemoBR123!",
        country="BR",
        company_name="eGarage Demo Brasil",
    ),
    DemoAccountSpec(
        username="demo_co",
        email="demo_co@egarage.cl",
        password="DemoCO123!",
        country="CO",
        company_name="eGarage Demo Colombia",
    ),
    DemoAccountSpec(
        username="demo_ec",
        email="demo_ec@egarage.cl",
        password="DemoEC123!",
        country="EC",
        company_name="eGarage Demo Ecuador",
    ),
    DemoAccountSpec(
        username="demo_mx",
        email="demo_mx@egarage.cl",
        password="DemoMX123!",
        country="MX",
        company_name="eGarage Demo Mexico",
    ),
    DemoAccountSpec(
        username="demo_pe",
        email="demo_pe@egarage.cl",
        password="DemoPE123!",
        country="PE",
        company_name="eGarage Demo Peru",
    ),
    DemoAccountSpec(
        username="demo_uy",
        email="demo_uy@egarage.cl",
        password="DemoUY123!",
        country="UY",
        company_name="eGarage Demo Uruguay",
    ),
)


PHONE_BY_COUNTRY = {
    "AR": "+54 11 5555 0101",
    "BR": "+55 11 5555 0102",
    "CL": "+56 9 5555 0103",
    "CO": "+57 300 555 0104",
    "EC": "+593 99 555 0105",
    "MX": "+52 55 5555 0106",
    "PE": "+51 999 555 0107",
    "US": "+1 555 555 0108",
    "UY": "+598 99 555 0109",
}


ADDRESS_BY_COUNTRY = {
    "AR": "Buenos Aires, Argentina",
    "BR": "Sao Paulo, Brasil",
    "CL": "Santiago, Chile",
    "CO": "Bogota, Colombia",
    "EC": "Guayaquil, Ecuador",
    "MX": "Ciudad de Mexico, Mexico",
    "PE": "Lima, Peru",
    "US": "Miami, Florida, USA",
    "UY": "Montevideo, Uruguay",
}


class Command(BaseCommand):
    help = "Crea o actualiza cuentas demo/test para todos los paises soportados."

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            action="append",
            dest="usernames",
            help="Limita la ejecucion a uno o varios usernames concretos.",
        )

    def handle(self, *args, **options):
        requested = set(options.get("usernames") or [])
        specs = [spec for spec in DEMO_ACCOUNTS if not requested or spec.username in requested]

        if not specs:
            self.stdout.write(self.style.WARNING("No hay cuentas para procesar con ese filtro."))
            return

        created_users = 0
        updated_users = 0
        created_companies = 0
        updated_companies = 0
        created_subscriptions = 0
        updated_subscriptions = 0
        created_emails = 0
        updated_emails = 0

        self.stdout.write(self.style.SUCCESS("Sincronizando cuentas demo/test..."))

        for spec in specs:
            with transaction.atomic():
                user, user_created = self._ensure_user(spec)
                email_address, email_created = self._ensure_email_address(user, spec)
                empresa, company_created = self._ensure_company(user, spec)
                suscripcion, subscription_created = self._ensure_subscription(user)

                created_users += int(user_created)
                updated_users += int(not user_created)
                created_emails += int(email_created)
                updated_emails += int(not email_created)
                created_companies += int(company_created)
                updated_companies += int(not company_created)
                created_subscriptions += int(subscription_created)
                updated_subscriptions += int(not subscription_created)

                self.stdout.write(
                    f"[OK] {spec.username} | user={'created' if user_created else 'updated'} | "
                    f"email={'created' if email_created else 'updated'} | "
                    f"empresa={'created' if company_created else 'updated'} | "
                    f"suscripcion={'created' if subscription_created else 'updated'} | "
                    f"pais={empresa.pais} | email={email_address.email}"
                )

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Resumen"))
        self.stdout.write(f"usuarios: {created_users} creados, {updated_users} actualizados")
        self.stdout.write(f"emails: {created_emails} creados, {updated_emails} actualizados")
        self.stdout.write(
            f"empresas: {created_companies} creadas, {updated_companies} actualizadas"
        )
        self.stdout.write(
            f"suscripciones: {created_subscriptions} creadas, {updated_subscriptions} actualizadas"
        )

    def _ensure_user(self, spec: DemoAccountSpec):
        User = get_user_model()
        user = User.objects.filter(username=spec.username).first()

        if user is None:
            user = User.objects.filter(email=spec.email).first()

        created = user is None
        if created:
            user = User.objects.create_user(
                username=spec.username,
                email=spec.email,
                password=spec.password,
                is_active=True,
            )

        first_name, last_name = self._split_names(spec)
        user.username = spec.username
        user.email = spec.email
        user.first_name = first_name
        user.last_name = last_name
        user.is_active = True
        user.set_password(spec.password)
        user.save()
        return user, created

    def _ensure_email_address(self, user, spec: DemoAccountSpec):
        EmailAddress.objects.filter(user=user).exclude(email__iexact=spec.email).update(
            primary=False
        )
        email_address, created = EmailAddress.objects.get_or_create(
            user=user,
            email=spec.email,
            defaults={"verified": True, "primary": True},
        )
        email_address.email = spec.email
        email_address.verified = True
        email_address.primary = True
        email_address.save()
        return email_address, created

    def _ensure_company(self, user, spec: DemoAccountSpec):
        now = timezone.now()
        company_defaults = self._company_defaults(spec, now)
        valid_fields = {field.name for field in Empresa._meta.fields}
        company_defaults = {
            field: value for field, value in company_defaults.items() if field in valid_fields
        }
        empresa, created = Empresa.objects.get_or_create(user=user, defaults=company_defaults)

        for field, value in company_defaults.items():
            setattr(empresa, field, value)
        empresa.save()
        return empresa, created

    def _ensure_subscription(self, user):
        today = timezone.now().date()
        one_year = today + timedelta(days=365)
        suscripcion, created = Suscripcion.objects.get_or_create(
            user=user,
            defaults={
                "tipo": "anual",
                "fecha_inicio": today,
                "fecha_fin": one_year,
                "activa": True,
            },
        )
        suscripcion.tipo = "anual"
        suscripcion.fecha_inicio = today
        suscripcion.fecha_fin = one_year
        suscripcion.activa = True
        suscripcion.save()
        return suscripcion, created

    def _company_defaults(self, spec: DemoAccountSpec, now):
        config = get_country_config(spec.country)
        currency = config.get("currency") or ("USD" if spec.country in {"US", "EC"} else "CLP")
        timezone_name = config.get("timezone") or "UTC"
        return {
            "nombre_taller": spec.company_name,
            "empresa": spec.company_name,
            "direccion": ADDRESS_BY_COUNTRY.get(spec.country, spec.company_name),
            "telefono": PHONE_BY_COUNTRY.get(spec.country, ""),
            "email": spec.email,
            "pais": spec.country,
            "zona_horaria": timezone_name,
            "moneda": currency,
            "plan": "premium",
            "suscripcion_activa": True,
            "fecha_inicio": now,
            "fecha_fin": now + timedelta(days=365),
            "valor_mensual": 0,
            "dias_prueba": 365,
            "trial_started_at": None,
            "trial_ends_at": None,
            "trial_already_used": True,
            "ha_usado_prueba": True,
            "onboarding_completado": True,
            "onboarding_step": 3,
            "onboarding_started_at": now,
            "onboarding_completed_at": now,
        }

    def _split_names(self, spec: DemoAccountSpec):
        if spec.username == "test_cl":
            return "Test", "Chile"
        if spec.username == "testuser_usa":
            return "Testuser", "USA"
        if spec.username.startswith("demo_"):
            return "Demo", spec.country
        return spec.username, ""
