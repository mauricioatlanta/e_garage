"""
python manage.py build_image_index \\
    --dirs /mnt/datos/media/productos /mnt/datos/imagenes /mnt/onedrive/catalogo \\
    --output /mnt/datos/image_index.json

Escanea los directorios indicados una sola vez y construye image_index.json,
un mapa {nombre_de_archivo (case-insensitive): [lista de rutas absolutas]}.

Una vez generado, pasarlo a import_monteazul_catalog con --image-index
para que la resolución de imágenes sea O(1) en lugar de O(n×glob).

Opciones:
    --dirs      Uno o más directorios a escanear (requerido, acepta múltiples valores)
    --output    Ruta donde escribir image_index.json (requerido).
                Para que aparezca automáticamente en Commerce Admin › Media Library,
                usar MEDIA_ROOT/commerce/image_index.json
    --stats     Muestra estadísticas detalladas después de construir el índice
"""
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Construye image_index.json escaneando directorios de imágenes."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dirs",
            nargs="+",
            required=True,
            metavar="DIR",
            help="Directorios a escanear (acepta múltiples rutas)",
        )
        parser.add_argument(
            "--output",
            required=True,
            metavar="PATH",
            help="Ruta de salida para image_index.json",
        )
        parser.add_argument(
            "--stats",
            action="store_true",
            help="Muestra estadísticas detalladas del índice generado",
        )

    def handle(self, *args, **options):
        from commerce.services.catalog.image_index import ImageIndexBuilder

        dirs = options["dirs"]
        output = options["output"]

        self.stdout.write(f"\nEscaneando {len(dirs)} directorio(s):")
        for d in dirs:
            self.stdout.write(f"  • {d}")
        self.stdout.write(f"Salida: {output}\n")

        try:
            builder = ImageIndexBuilder(search_roots=dirs, output_path=output)
            index = builder.build()
        except Exception as exc:
            raise CommandError(f"Error construyendo índice: {exc}") from exc

        stats = ImageIndexBuilder.stats(index)
        self.stdout.write(
            self.style.SUCCESS(
                f"\n✔ Índice construido:\n"
                f"   Archivos totales:  {stats['total_files']}\n"
                f"   Nombres únicos:    {stats['unique_names']}\n"
                f"   Nombres ambiguos:  {stats['ambiguous_names']}\n"
            )
        )

        if options["stats"] and stats["ambiguous_names"]:
            self.stdout.write(self.style.WARNING("\nNombres ambiguos (múltiples rutas):"))
            for name, paths in sorted(index.items()):
                if len(paths) > 1:
                    self.stdout.write(f"  {name}:")
                    for p in paths:
                        self.stdout.write(f"    → {p}")

        if stats["ambiguous_names"]:
            self.stdout.write(
                self.style.WARNING(
                    f"\n⚠ {stats['ambiguous_names']} nombre(s) ambiguo(s). "
                    "Usa --stats para ver cuáles. "
                    "Durante la importación se usará la primera ruta (orden lexicográfico).\n"
                )
            )
