"""Management command para mostrar la versión del sistema eGarage."""

from django.core.management.base import BaseCommand

from taller.version import CHANGELOG, __release_date__, __version__, __version_info__


class Command(BaseCommand):
    help = "Muestra la versión actual de eGarage (no confundir con Django version)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--changelog",
            action="store_true",
            help="Muestra el changelog completo",
        )

    def handle(self, *args, **options):
        self.stdout.write("=" * 80)
        self.stdout.write(
            self.style.SUCCESS(
                "  🚀 eGarage - Sistema de Gestión de Talleres Automotrices"
            )
        )
        self.stdout.write("=" * 80)
        self.stdout.write("")
        self.stdout.write(f"  📦 Versión: {self.style.SUCCESS(__version__)}")
        self.stdout.write(f"  📅 Fecha de Release: {__release_date__}")
        self.stdout.write(f"  🏷️  Version Info: {__version_info__}")
        self.stdout.write("")
        self.stdout.write("=" * 80)

        if options["changelog"]:
            self.stdout.write("")
            self.stdout.write(CHANGELOG)
            self.stdout.write("")
            self.stdout.write("=" * 80)
        else:
            self.stdout.write("")
            self.stdout.write("💡 Para ver el changelog completo, ejecuta:")
            self.stdout.write("   python manage.py version --changelog")
            self.stdout.write("")
            self.stdout.write("   O visita: http://127.0.0.1:8000/changelog/")
            self.stdout.write("")
            self.stdout.write("=" * 80)
