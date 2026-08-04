"""
python manage.py commerce_seed --empresa 2

Crea CommerceCategory y CommerceProduct para todos los repuestos de la empresa.
Publica automáticamente los que tienen stock > 0.

Opciones:
    --empresa     ID de la Empresa a sembrar (requerido)
    --dry-run     Muestra lo que haría sin guardar nada
    --no-publish  No publicar productos aunque tengan stock
"""
from django.core.management.base import BaseCommand, CommandError

from commerce.services.sync import SyncCommerceCatalogService


class Command(BaseCommand):
    help = "Siembra CommerceCategory y CommerceProduct desde el ERP para una empresa."

    def add_arguments(self, parser):
        parser.add_argument("--empresa", type=int, required=True, help="ID de la Empresa")
        parser.add_argument("--dry-run", action="store_true", help="Solo muestra; no guarda")
        parser.add_argument("--no-publish", action="store_true", help="No publica productos con stock")

    def handle(self, *args, **options):
        empresa_id = options["empresa"]
        dry_run = options["dry_run"]
        publish_with_stock = not options["no_publish"]

        from taller.models import Empresa
        try:
            empresa = Empresa.objects.get(pk=empresa_id)
        except Empresa.DoesNotExist:
            raise CommandError(f"No existe Empresa con id={empresa_id}")

        self.stdout.write(f"\n{'[DRY RUN] ' if dry_run else ''}Sembrando Commerce para: {empresa.nombre}\n")

        service = SyncCommerceCatalogService(empresa)
        result = service.sync_all(publish_with_stock=publish_with_stock, dry_run=dry_run)

        if result.errors:
            self.stderr.write("\nErrores:")
            for e in result.errors:
                self.stderr.write(f"  ✗ {e}")

        if not dry_run:
            self.stdout.write(self.style.SUCCESS(
                f"\n✔ {result}\n"
            ))
        else:
            self.stdout.write("\n[dry-run completado — no se guardó nada]\n")
