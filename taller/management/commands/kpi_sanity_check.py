from django.core.management.base import BaseCommand
from django.db.models import DecimalField, ExpressionWrapper, F, Sum
from django.utils import timezone

from taller.models import Documento, LineaServicio, Tecnico


class Command(BaseCommand):
    help = "KPI sanity check usando solo fecha_emision"

    def handle(self, *args, **options):
        self.stdout.write("📊 Ejecutando KPI sanity check...")

        try:
            # KPI 1: Totales por técnico en el mes actual
            self.stdout.write("\n1. Totales por técnico en el mes actual:")
            monto = ExpressionWrapper(
                F("cantidad") * F("precio_unitario") * (1 - F("descuento")),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            )

            totales = (
                LineaServicio.objects.filter(
                    documento__fecha_emision__month=timezone.now().month
                )
                .annotate(monto=monto)
                .values("documento__tecnico_responsable__nombre")
                .annotate(total=Sum("monto"))
            )

            self.stdout.write("   Resultados:")
            for total in totales:
                self.stdout.write(
                    f"   - {total['documento__tecnico_responsable__nombre']}: ${total['total']}"
                )

            # KPI 2: Documentos por estado en el mes actual
            self.stdout.write("\n2. Documentos por estado en el mes actual:")
            docs_por_estado = (
                Documento.objects.filter(fecha_emision__month=timezone.now().month)
                .values("estado")
                .annotate(total=Sum("id"))
            )

            self.stdout.write("   Resultados:")
            for estado in docs_por_estado:
                self.stdout.write(
                    f"   - {estado['estado']}: {estado['total']} documentos"
                )

            # KPI 3: Técnicos más activos
            self.stdout.write("\n3. Técnicos más activos:")
            tecnicos_activos = (
                Tecnico.objects.filter(
                    documento__fecha_emision__month=timezone.now().month
                )
                .values("nombre")
                .annotate(total_docs=Sum("documento__id"))
            )

            self.stdout.write("   Resultados:")
            for tecnico in tecnicos_activos:
                self.stdout.write(
                    f"   - {tecnico['nombre']}: {tecnico['total_docs']} documentos"
                )

            self.stdout.write(self.style.SUCCESS("\n✅ KPI sanity check completado"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error en KPI sanity check: {e}"))
            raise
