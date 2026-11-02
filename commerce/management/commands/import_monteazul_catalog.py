"""
python manage.py import_monteazul_catalog --db /ruta/catalog.sqlite3 --empresa 2

Importa el catálogo de productos MonteAzul desde una BD SQLite.
Tablas leídas: catalog_category, catalog_product, catalog_productimage.

Si hay imágenes ambiguas o faltantes se escribe manual_review.json
(por defecto en el mismo directorio que --db; sobreescribible con --review-output).

Opciones:
    --empresa           ID de la Empresa destino (requerido)
    --db                Ruta al archivo SQLite de MonteAzul (requerido)
    --overwrite         Actualiza registros existentes (sin esto conserva cambios manuales)
    --dry-run           Muestra lo que importaría sin guardar nada
    --only-categories   Solo importa categorías
    --only-products     Solo importa repuestos y productos Commerce
    --only-images       Solo importa imágenes (requiere que los productos ya existan)
    --review-output     Ruta del manual_review.json (default: directorio de --db)
"""
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Importa el catálogo de productos MonteAzul desde una BD SQLite."

    def add_arguments(self, parser):
        parser.add_argument("--db", required=True, help="Ruta al archivo SQLite de MonteAzul")
        parser.add_argument("--empresa", type=int, required=True, help="ID de la Empresa destino")
        parser.add_argument(
            "--overwrite", action="store_true",
            help="Actualiza categorías y productos existentes (sin esto los conserva)",
        )
        parser.add_argument(
            "--dry-run", action="store_true",
            help="Muestra lo que importaría sin guardar nada",
        )
        parser.add_argument(
            "--only-categories", action="store_true",
            help="Solo importa categorías",
        )
        parser.add_argument(
            "--only-products", action="store_true",
            help="Solo importa repuestos y productos Commerce",
        )
        parser.add_argument(
            "--only-images", action="store_true",
            help="Solo importa imágenes (los productos deben existir ya)",
        )
        parser.add_argument(
            "--review-output", default=None,
            help="Ruta del manual_review.json. "
                 "Default: MEDIA_ROOT/commerce/manual_review.json (visible en Commerce Admin › Media).",
        )
        parser.add_argument(
            "--image-index", default=None,
            help="Ruta a image_index.json generado por build_image_index. "
                 "Acelera la resolución de imágenes de O(n×glob) a O(1).",
        )

    def handle(self, *args, **options):
        from django.conf import settings
        from taller.models import Empresa
        from commerce.services.catalog.adapters.monteazul import MonteAzulAdapter

        try:
            empresa = Empresa.objects.get(pk=options["empresa"])
        except Empresa.DoesNotExist:
            raise CommandError(f"No existe Empresa con id={options['empresa']}")

        dry_run = options["dry_run"]
        prefix = "[DRY RUN] " if dry_run else ""

        # Default review output: MEDIA_ROOT/commerce/manual_review.json
        # → aparece automáticamente en Commerce Admin › Media Library
        review_output = options["review_output"]
        if not review_output and not dry_run:
            from pathlib import Path
            review_output = str(
                Path(settings.MEDIA_ROOT) / "commerce" / "manual_review.json"
            )

        self.stdout.write(
            f"\n{prefix}Importando catálogo MonteAzul para: {empresa.nombre_taller}\n"
            f"BD SQLite: {options['db']}\n"
        )

        importer = MonteAzulAdapter(
            db_path=options["db"],
            empresa=empresa,
            dry_run=dry_run,
            overwrite=options["overwrite"],
            only_categories=options["only_categories"],
            only_products=options["only_products"],
            only_images=options["only_images"],
            review_output=review_output,
            image_index_path=options["image_index"],
        )

        try:
            result = importer.run()
        except FileNotFoundError as exc:
            raise CommandError(str(exc))
        except ValueError as exc:
            raise CommandError(str(exc))

        if result.errors:
            self.stderr.write("\nAvisos / Errores:")
            for msg in result.errors:
                self.stderr.write(f"  • {msg}")

        if dry_run:
            self.stdout.write("\n[dry-run completado — no se guardó nada]\n")
        else:
            self.stdout.write(self.style.SUCCESS(f"\n✔ {result}\n"))
            if result.review_written_to:
                self.stdout.write(
                    self.style.WARNING(
                        f"\n⚠ Hay imágenes ambiguas o faltantes. "
                        f"Revisar: {result.review_written_to}\n"
                    )
                )
