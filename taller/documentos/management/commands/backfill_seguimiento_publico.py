"""
Comando de backfill para generar SeguimientoPublico en documentos existentes.
"""

from django.core.management.base import BaseCommand

from taller.models.documento import Documento
from taller.models.memoria_seguimiento import SeguimientoPublico


class Command(BaseCommand):
    help = "Genera SeguimientoPublico para documentos existentes que no lo tengan"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Solo muestra lo que se haría sin hacer cambios",
        )
        parser.add_argument(
            "--empresa-id",
            type=int,
            help="ID de empresa específica (opcional, por defecto todas)",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        empresa_id = options.get("empresa_id")

        # Filtrar documentos
        documentos = Documento.objects.all()
        if empresa_id:
            documentos = documentos.filter(empresa_id=empresa_id)

        # Excluir documentos que ya tienen seguimiento público
        documentos_sin_seguimiento = documentos.filter(seguimiento_publico__isnull=True)

        count = documentos_sin_seguimiento.count()
        created = 0

        self.stdout.write(self.style.SUCCESS(f"🔄 Iniciando backfill de seguimiento público..."))
        if dry_run:
            self.stdout.write(self.style.WARNING("⚠️  MODO DRY-RUN - No se harán cambios"))

        self.stdout.write(f"📊 Documentos sin seguimiento: {count}")

        for documento in documentos_sin_seguimiento.select_related("empresa"):
            self.stdout.write(
                f"  📄 Documento {documento.numero_documento} (ID: {documento.id}) - Empresa: {documento.empresa.nombre_taller}"
            )

            if not dry_run:
                seguimiento, created_now = SeguimientoPublico.objects.get_or_create(
                    documento=documento,
                    defaults={
                        "empresa": documento.empresa,
                        "activo": True,
                    },
                )
                if created_now:
                    created += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"    ✅ Seguimiento creado - Token: {seguimiento.token[:16]}..."
                        )
                    )
                else:
                    self.stdout.write(self.style.WARNING("    ⚠️  Seguimiento ya existía"))
            else:
                created += 1

        if dry_run:
            self.stdout.write(
                self.style.WARNING(f"✅ DRY-RUN completado: {created} seguimientos se crearían")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Backfill completado: {created} seguimientos creados de {count} documentos"
                )
            )
