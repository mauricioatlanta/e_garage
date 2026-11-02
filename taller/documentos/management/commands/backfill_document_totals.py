from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db.models import DecimalField, ExpressionWrapper, F, Sum

from taller.models.documento import Documento


class Command(BaseCommand):
    help = "Recalcula totales de documentos (partes, servicios, impuestos)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Solo muestra lo que se haría sin hacer cambios",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        count = 0
        updated = 0

        self.stdout.write(self.style.SUCCESS("🔄 Iniciando recálculo de totales de documentos..."))
        if dry_run:
            self.stdout.write(self.style.WARNING("⚠️  MODO DRY-RUN - No se harán cambios"))

        for doc in Documento.objects.all().prefetch_related(
            "lineas_repuesto", "lineas_servicio", "lineas_otro_servicio"
        ):
            count += 1

            # Calcular totales usando aggregates
            sum_rep = doc.lineas_repuesto.aggregate(
                total=Sum(
                    ExpressionWrapper(
                        F("cantidad") * F("precio_unitario"),
                        output_field=DecimalField(max_digits=12, decimal_places=2),
                    )
                )
            )["total"] or Decimal("0.00")

            sum_serv = doc.lineas_servicio.aggregate(total=Sum("precio_unitario"))[
                "total"
            ] or Decimal("0.00")

            sum_otros = doc.lineas_otro_servicio.aggregate(total=Sum("precio_cliente"))[
                "total"
            ] or Decimal("0.00")

            subtotal = sum_rep + sum_serv + sum_otros

            # Calcular IVA (19% solo sobre repuestos según lógica de negocio CL)
            # Para US sería sobre el subtotal total, pero por simplicidad mantenemos CL
            tax_rate = Decimal("0.19") if doc.country == "CL" else Decimal("0.08")
            base_tax = sum_rep if doc.country == "CL" else subtotal
            iva = base_tax * tax_rate if getattr(doc, "incluir_iva", True) else Decimal("0.00")
            total = subtotal + iva

            # Verificar si necesita actualización
            needs_update = (
                doc.neto_repuestos != sum_rep
                or doc.neto_servicios != sum_serv
                or doc.neto_otros_servicios != sum_otros
                or doc.tax_amount != iva
                or doc.total != total
            )

            if needs_update:
                self.stdout.write(
                    f"📄 Documento {doc.numero_documento or doc.id}: "
                    f"Rep: ${sum_rep} | Serv: ${sum_serv} | Otros: ${sum_otros} | "
                    f"IVA: ${iva} | Total: ${total}"
                )

                if not dry_run:
                    doc.neto_repuestos = sum_rep
                    doc.neto_servicios = sum_serv
                    doc.neto_otros_servicios = sum_otros
                    doc.tax_amount = iva
                    doc.total = total
                    doc.save(
                        update_fields=[
                            "neto_repuestos",
                            "neto_servicios",
                            "neto_otros_servicios",
                            "tax_amount",
                            "total",
                        ]
                    )
                    updated += 1

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"✅ DRY-RUN completado: {count} documentos revisados, {updated} necesitarían actualización"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Recálculo completado: {updated} de {count} documentos actualizados"
                )
            )
