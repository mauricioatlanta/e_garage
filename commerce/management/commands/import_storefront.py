"""
python manage.py import_storefront --adapter monteazul --empresa 2

Importa contenido de storefront (branding, páginas, FAQs) desde un adaptador.
Cada adaptador vive en commerce/importers/<nombre>.py y expone una clase Importer.

Opciones:
    --adapter    Nombre del adaptador (requerido). Ej: monteazul
    --empresa    ID de la Empresa destino (requerido)
    --source     Ruta al archivo de datos del adaptador (opcional)
    --dry-run    Muestra lo que haría sin guardar nada

Para agregar un nuevo cliente:
    cp commerce/importers/monteazul.py commerce/importers/otro_cliente.py
    # editar defaults y lógica
    python manage.py import_storefront --adapter otro_cliente --empresa 5
"""
import importlib

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Importa contenido de storefront desde un adaptador."

    def add_arguments(self, parser):
        parser.add_argument("--adapter", required=True, help="Nombre del adaptador (ej: monteazul)")
        parser.add_argument("--empresa", type=int, required=True, help="ID de la Empresa destino")
        parser.add_argument("--source", default=None, help="Ruta al directorio fuente del proyecto")
        parser.add_argument("--dry-run", action="store_true", help="Solo muestra; no guarda ni copia archivos")
        parser.add_argument("--overwrite", action="store_true", help="Reemplaza datos existentes (sin esto, conserva cambios manuales)")

    def handle(self, *args, **options):
        adapter_name = options["adapter"]
        empresa_id = options["empresa"]
        source = options["source"]
        dry_run = options["dry_run"]
        overwrite = options["overwrite"]

        from taller.models import Empresa
        try:
            empresa = Empresa.objects.get(pk=empresa_id)
        except Empresa.DoesNotExist:
            raise CommandError(f"No existe Empresa con id={empresa_id}")

        module_path = f"commerce.importers.{adapter_name}"
        try:
            module = importlib.import_module(module_path)
            Importer = getattr(module, "Importer")
        except ImportError:
            raise CommandError(
                f"Adaptador '{adapter_name}' no encontrado. "
                f"Crea commerce/importers/{adapter_name}.py con una clase Importer."
            )
        except AttributeError:
            raise CommandError(
                f"El módulo commerce/importers/{adapter_name}.py no expone una clase 'Importer'."
            )

        prefix = "[DRY RUN] " if dry_run else ""
        self.stdout.write(f"\n{prefix}Importando storefront para: {empresa.nombre}\n")
        self.stdout.write(f"Adaptador: {adapter_name}\n")

        importer = Importer(empresa, source=source, dry_run=dry_run, overwrite=overwrite)
        try:
            result = importer.run()
        except FileNotFoundError as exc:
            raise CommandError(str(exc))

        if result.errors:
            self.stderr.write("\nAvisos / Errores:")
            for msg in result.errors:
                self.stderr.write(f"  • {msg}")

        if not dry_run:
            self.stdout.write(self.style.SUCCESS(f"\n✔ {result}\n"))
        else:
            self.stdout.write("\n[dry-run completado — no se guardó nada]\n")
