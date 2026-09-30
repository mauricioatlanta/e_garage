"""Create the canonical USA QA tenants without seeding functional data."""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from taller.config.country_settings import CountrySettings
from taller.models.configuracion import ConfiguracionEmpresa
from taller.models.empresa import Empresa
from taller.utils.country_config import get_country_config
from taller.utils.plan_catalog import PLAN_GROWTH


USA_QA_TENANTS = (
    {
        "username": "vc_us_workshop",
        "email": "vc_us_workshop@demo.egarage.com",
        "name": "Validation Workshop USA",
        "rubro": "WORKSHOP",
    },
    {
        "username": "vc_us_salvage",
        "email": "vc_us_salvage@demo.egarage.com",
        "name": "Validation Salvage Yard USA",
        "rubro": "DESARMADURIA",
    },
    {
        "username": "vc_us_parts",
        "email": "vc_us_parts@demo.egarage.com",
        "name": "Validation Auto Parts USA",
        "rubro": "PARTS",
    },
    {
        "username": "vc_us_tire",
        "email": "vc_us_tire@demo.egarage.com",
        "name": "Validation Tire Shop USA",
        "rubro": "TIRE",
    },
)


class Command(BaseCommand):
    help = "Create or verify the canonical USA QA tenants (without seed data)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--country",
            default="US",
            choices=["US"],
            help="Country to prepare. Only US is supported in this phase.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show the planned changes without writing anything.",
        )

    def handle(self, *args, **options):
        country = options["country"].upper()
        dry_run = options["dry_run"]
        checks = self._preflight(country)

        errors = [check["error"] for check in checks if check["error"]]
        if errors:
            raise CommandError("\n".join(errors))

        for check in checks:
            action = "reutilizar/verificar" if check["user"] else "crear"
            prefix = "[DRY-RUN] " if dry_run else ""
            self.stdout.write(
                f"{prefix}{action}: {check['spec']['username']} -> "
                f"{check['spec']['name']} ({check['spec']['rubro']})"
            )

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry-run: no se escribieron datos."))
            return

        with transaction.atomic():
            for check in checks:
                if check["user"] is None:
                    self._create_tenant(check["spec"], country)

        self.stdout.write(self.style.SUCCESS("Tenants QA USA listos."))

    def _preflight(self, country):
        User = get_user_model()
        country_config = get_country_config(country)
        checks = []

        for spec in USA_QA_TENANTS:
            username = spec["username"]
            user = User.objects.filter(username=username).first()
            error = None

            if user is None:
                if Empresa.objects.filter(nombre_taller=spec["name"]).exists():
                    error = (
                        f"Colisión de nombre para {username}: ya existe una empresa "
                        f"llamada {spec['name']!r}. No se modificará."
                    )
            else:
                error = self._validate_existing_user(user, spec, country, country_config)

            checks.append({"spec": spec, "user": user, "error": error})

        return checks

    def _validate_existing_user(self, user, spec, country, country_config):
        if (user.email or "").strip().lower() != spec["email"]:
            return f"Colisión incompatible: {spec['username']} tiene otro email."
        if not user.is_active or user.is_staff or user.is_superuser:
            return f"Colisión incompatible: estado no QA en {spec['username']}."

        try:
            empresa = user.empresa
        except Empresa.DoesNotExist:
            return f"Colisión incompatible: {spec['username']} no tiene empresa."

        expected = {
            "nombre_taller": spec["name"],
            "pais": country,
            "moneda": country_config["currency"],
            "plan": PLAN_GROWTH,
            "suscripcion_activa": True,
            "zona_horaria": country_config["timezone"],
        }
        for field, value in expected.items():
            if getattr(empresa, field) != value:
                return (
                    f"Colisión incompatible: {spec['username']} tiene "
                    f"{field}={getattr(empresa, field)!r}; esperaba {value!r}."
                )

        try:
            config = empresa.config
        except ConfiguracionEmpresa.DoesNotExist:
            return f"Colisión incompatible: {spec['username']} no tiene configuración."

        config_expected = {
            "moneda": country_config["currency"],
            "tasa_impuesto": country_config["tax_rate"],
            "sales_tax_rate": country_config["tax_rate"],
            "aplicar_impuesto_por_defecto": False,
            "rubro_principal": spec["rubro"],
            "rubros": [spec["rubro"]],
        }
        for field, value in config_expected.items():
            if getattr(config, field) != value:
                return (
                    f"Colisión incompatible: configuración de {spec['username']} "
                    f"tiene {field}={getattr(config, field)!r}; esperaba {value!r}."
                )
        if config.modules_configured_at is None:
            return f"Colisión incompatible: configuración incompleta en {spec['username']}."

        return None

    def _create_tenant(self, spec, country):
        User = get_user_model()
        country_config = get_country_config(country)
        user = User.objects.create(
            username=spec["username"],
            email=spec["email"],
            is_active=True,
            is_staff=False,
            is_superuser=False,
        )
        user.set_unusable_password()
        user.save(update_fields=["password"])

        empresa = Empresa.objects.create(
            user=user,
            nombre_taller=spec["name"],
            empresa=spec["name"],
            email=spec["email"],
            pais=country,
            moneda=country_config["currency"],
            zona_horaria=country_config["timezone"],
            plan=PLAN_GROWTH,
            suscripcion_activa=True,
            onboarding_completado=True,
        )
        ConfiguracionEmpresa.objects.create(
            empresa=empresa,
            nombre_publico=spec["name"],
            tagline=f"{spec['rubro']} — Validation Center USA",
            moneda=country_config["currency"],
            tasa_impuesto=country_config["tax_rate"],
            sales_tax_rate=country_config["tax_rate"],
            aplicar_impuesto_por_defecto=False,
            rubro_principal=spec["rubro"],
            rubros=[spec["rubro"]],
            modules_configured_at=timezone.now(),
        )


def _validate_country_definition():
    """Keep the command tied to official country/rubro choices at import time."""
    valid_countries = {value for value, _label in CountrySettings.COUNTRIES.items()}
    if "US" not in valid_countries:
        raise RuntimeError("US no existe en la configuración oficial de países")


_validate_country_definition()
