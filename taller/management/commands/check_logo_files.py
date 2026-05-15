"""
Management command para verificar logos físicos en el sistema de archivos.
No requiere acceso a la base de datos.
"""

from django.core.management.base import BaseCommand
from django.conf import settings
import os
import glob


class Command(BaseCommand):
    help = "Verifica archivos de logo físicos en el sistema de archivos"

    def handle(self, *args, **options):
        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS("🔍 DIAGNÓSTICO DE ARCHIVOS DE LOGO"))
        self.stdout.write("=" * 80)

        # Ruta donde se guardan los logos
        media_root = getattr(settings, "MEDIA_ROOT", None)
        if not media_root:
            self.stdout.write(self.style.ERROR("\n❌ MEDIA_ROOT no está configurado en settings"))
            return

        logo_dir = os.path.join(media_root, "company_logos")
        self.stdout.write(f"\n📁 Buscando logos en: {logo_dir}")

        if not os.path.exists(logo_dir):
            self.stdout.write(self.style.WARNING(f"\n⚠️  El directorio {logo_dir} no existe"))
            return

        # Buscar todos los archivos de imagen
        image_extensions = ["*.png", "*.jpg", "*.jpeg", "*.svg", "*.webp", "*.jfif"]
        logo_files = []
        for ext in image_extensions:
            logo_files.extend(glob.glob(os.path.join(logo_dir, ext)))
            logo_files.extend(glob.glob(os.path.join(logo_dir, ext.upper())))

        if not logo_files:
            self.stdout.write(
                self.style.WARNING(f"\n⚠️  No se encontraron archivos de logo en {logo_dir}")
            )
            return

        self.stdout.write(f"\n📊 Total de archivos encontrados: {len(logo_files)}\n")

        for logo_path in sorted(logo_files):
            filename = os.path.basename(logo_path)
            file_size = os.path.getsize(logo_path) / 1024  # KB
            relative_path = os.path.relpath(logo_path, media_root)
            media_url = getattr(settings, "MEDIA_URL", "/media/")
            url_path = f"{media_url}{relative_path}".replace("\\", "/")

            self.stdout.write(f"\n{'='*60}")
            self.stdout.write(f"📄 Archivo: {filename}")
            self.stdout.write(f"   Ruta completa: {logo_path}")
            self.stdout.write(f"   Ruta relativa: {relative_path}")
            self.stdout.write(f"   URL relativa: {url_path}")
            self.stdout.write(f"   Tamaño: {file_size:.2f} KB")
            self.stdout.write(f"   URL absoluta (ejemplo): https://www.egarage.cl{url_path}")
            self.stdout.write(f"{'='*60}")

        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(self.style.SUCCESS("✅ DIAGNÓSTICO COMPLETADO"))
        self.stdout.write("=" * 80)
        self.stdout.write("\n")
