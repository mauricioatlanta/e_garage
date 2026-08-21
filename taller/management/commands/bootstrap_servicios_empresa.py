from django.core.management.base import BaseCommand, CommandError

from taller.models.empresa import Empresa
from taller.servicios.catalog_bootstrap import ensure_company_services_catalog


class Command(BaseCommand):
    help = (
        "Bootstrapea el catálogo maestro de servicios para una empresa. "
        "Flujo explícito y controlado: no se ejecuta automáticamente desde vistas."
    )

    def add_arguments(self, parser):
        parser.add_argument("empresa_id", type=int)
        parser.add_argument(
            "--country",
            type=str,
            default=None,
            help="Código de país a usar (por defecto, el país de la empresa).",
        )

    def handle(self, *args, **options):
        empresa_id = options["empresa_id"]
        try:
            empresa = Empresa.objects.get(pk=empresa_id)
        except Empresa.DoesNotExist:
            raise CommandError(f"Empresa {empresa_id} no existe")

        country_code = options["country"] or empresa.pais
        created = ensure_company_services_catalog(empresa, country_code)
        self.stdout.write(
            self.style.SUCCESS(
                f"Empresa {empresa_id} ({country_code}): {created} servicios creados"
            )
        )
