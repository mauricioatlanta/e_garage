"""
Comando para recalcular totales de documentos existentes con total=0.

Causa raíz: los documentos se guardaban sin llamar a recompute_totals()
después de crear las líneas, dejando total=0.

Uso:
  python manage.py fix_documento_totales
  python manage.py fix_documento_totales --dry-run
  python manage.py fix_documento_totales --empresa-id 1
"""

from decimal import Decimal

from django.core.management.base import BaseCommand

from taller.models import Documento


class Command(BaseCommand):
    help = "Recalcula totales de documentos que tienen total=0 pero tienen líneas"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Mostrar qué documentos se corregirían sin hacer cambios",
        )
        parser.add_argument(
            "--empresa-id",
            type=int,
            help="Procesar solo documentos de esta empresa",
        )

    def handle(self, *args, **options):
        dry_run = options.get("dry_run", False)
        empresa_id = options.get("empresa_id")

        qs = Documento.objects.select_related("empresa").prefetch_related(
            "lineas_repuesto",
            "lineas_servicio",
            "lineas_otro_servicio",
        )

        if empresa_id:
            qs = qs.filter(empresa_id=empresa_id)
            self.stdout.write(f"📋 Procesando solo empresa_id={empresa_id}")

        # Filtrar documentos con total=0 que tengan al menos una línea
        documentos_a_revisar = []
        for doc in qs:
            total_lineas = (
                doc.lineas_repuesto.count()
                + doc.lineas_servicio.count()
                + doc.lineas_otro_servicio.count()
            )
            if doc.total == Decimal("0") and total_lineas > 0:
                documentos_a_revisar.append((doc, total_lineas))

        if not documentos_a_revisar:
            self.stdout.write(
                self.style.SUCCESS("✅ No hay documentos con total=0 que tengan líneas.")
            )
            return

        self.stdout.write(
            f"📋 Encontrados {len(documentos_a_revisar)} documentos con total=0 y líneas."
        )

        if dry_run:
            self.stdout.write(self.style.WARNING("🔍 Modo dry-run: no se aplicarán cambios.\n"))
            for doc, total_lineas in documentos_a_revisar[:20]:
                self.stdout.write(
                    f"  - ID {doc.id} | {doc.tipo} #{doc.numero} | "
                    f"fecha={doc.fecha_emision} | líneas={total_lineas}"
                )
            if len(documentos_a_revisar) > 20:
                self.stdout.write(f"  ... y {len(documentos_a_revisar) - 20} más")
            return

        actualizados = 0
        errores = 0
        for doc, total_lineas in documentos_a_revisar:
            try:
                doc.recompute_totals(persist=True)
                actualizados += 1
                self.stdout.write(f"  ✓ ID {doc.id} | total actualizado a {doc.total}")
            except Exception as e:
                errores += 1
                self.stdout.write(self.style.ERROR(f"  ✗ ID {doc.id} | Error: {e}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Completado: {actualizados} documentos actualizados, {errores} errores."
            )
        )
