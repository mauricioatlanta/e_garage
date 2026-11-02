"""
Comando para verificar que los reportes de mecánicos están calculando correctamente los totales
Uso: python manage.py verificar_reportes_mecanicos --company "NOMBRE_EMPRESA"
"""

from datetime import date, timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db.models import F, Sum

from taller.models import Documento, Empresa, LineaServicio, Tecnico


class Command(BaseCommand):
    help = "Verifica que los reportes de mecánicos están calculando correctamente los totales"

    def add_arguments(self, parser):
        parser.add_argument(
            "--company",
            type=str,
            help="Nombre de la empresa (opcional, si no se especifica se procesan todas)",
            required=False,
        )
        parser.add_argument(
            "--days",
            type=int,
            default=30,
            help="Número de días hacia atrás para el análisis (default: 30)",
        )

    def handle(self, *args, **options):
        company_name = options.get("company")
        days = options.get("days")

        self.stdout.write(
            self.style.SUCCESS(f"🔍 Verificando reportes de mecánicos (últimos {days} días)...")
        )

        # Calcular fechas
        fecha_hasta = date.today()
        fecha_desde = fecha_hasta - timedelta(days=days)

        # Obtener empresa(s)
        if company_name:
            try:
                empresas = [Empresa.objects.get(nombre_taller__icontains=company_name)]
                self.stdout.write(f"📋 Procesando empresa: {empresas[0].nombre_taller}")
            except Empresa.DoesNotExist:
                raise CommandError(
                    f"❌ No se encontró empresa con nombre que contenga: {company_name}"
                )
        else:
            empresas = Empresa.objects.all()
            self.stdout.write(f"📋 Procesando todas las empresas ({empresas.count()} empresas)")

        for empresa in empresas:
            self.stdout.write(f"\n🏢 Empresa: {empresa.nombre_taller}")
            self.stdout.write(f"📅 Período: {fecha_desde} a {fecha_hasta}")

            # Obtener documentos de la empresa en el período
            documentos = Documento.objects.filter(
                fecha_emision__range=[fecha_desde, fecha_hasta],
                tecnico_responsable__isnull=False,
                empresa=empresa,
                tipo="FAC",
            ).select_related("tecnico_responsable")

            self.stdout.write(f"📄 Documentos encontrados: {documentos.count()}")

            if documentos.count() == 0:
                self.stdout.write("   ⚠️ No hay documentos en este período")
                continue

            # Obtener técnicos de la empresa
            tecnicos = Tecnico.objects.filter(empresa=empresa).order_by("nombre")

            for tecnico in tecnicos:
                self.stdout.write(f"\n🔧 Técnico: {tecnico.nombre}")

                # Documentos del técnico
                docs_tecnico = documentos.filter(tecnico_responsable=tecnico)
                total_docs = docs_tecnico.count()

                if total_docs == 0:
                    self.stdout.write("   ⚠️ Sin documentos en este período")
                    continue

                # Servicios del técnico
                servicios_tecnico = LineaServicio.objects.filter(documento__in=docs_tecnico)
                total_servicios = servicios_tecnico.count()

                # Cálculo correcto del total generado
                total_generado = (
                    servicios_tecnico.aggregate(
                        total=Sum(F("cantidad") * F("precio_unitario") * (1 - F("descuento") / 100))
                    )["total"]
                    or 0
                )

                # Promedio por documento
                promedio_doc = round(total_generado / total_docs if total_docs > 0 else 0, 0)

                # Mostrar resultados
                self.stdout.write(f"   📋 Documentos: {total_docs}")
                self.stdout.write(f"   ⚙️ Servicios: {total_servicios}")
                self.stdout.write(f"   💰 Total generado: ${total_generado:,.0f}")
                self.stdout.write(f"   📊 Promedio/doc: ${promedio_doc:,.0f}")

                # Verificar algunos documentos específicos
                if total_docs > 0:
                    self.stdout.write("   📋 Detalle de documentos:")
                    for doc in docs_tecnico[:3]:  # Mostrar solo los primeros 3
                        servicios_doc = LineaServicio.objects.filter(documento=doc)
                        total_doc = (
                            servicios_doc.aggregate(
                                total=Sum(
                                    F("cantidad")
                                    * F("precio_unitario")
                                    * (1 - F("descuento") / 100)
                                )
                            )["total"]
                            or 0
                        )
                        self.stdout.write(
                            f"      - {doc.tipo} #{doc.numero}: ${total_doc:,.0f} ({servicios_doc.count()} servicios)"
                        )

                    if total_docs > 3:
                        self.stdout.write(f"      ... y {total_docs - 3} documentos más")

        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(self.style.SUCCESS("✅ Verificación completada"))
