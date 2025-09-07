"""
Comando para marcar todos los documentos como pagados
Uso: python manage.py marcar_documentos_pagados --company "NOMBRE_EMPRESA"
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from taller.models import Documento, Empresa


class Command(BaseCommand):
    help = "Marca todos los documentos de una empresa como pagados"

    def add_arguments(self, parser):
        parser.add_argument(
            "--company",
            type=str,
            help="Nombre de la empresa (opcional, si no se especifica se procesan todas)",
            required=False,
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Mostrar qué documentos se marcarían como pagados sin hacer cambios",
        )

    def handle(self, *args, **options):
        company_name = options.get("company")
        dry_run = options.get("dry_run")

        self.stdout.write(
            self.style.SUCCESS(
                "🚀 Iniciando proceso de marcado de documentos como pagados..."
            )
        )

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
            self.stdout.write(
                f"📋 Procesando todas las empresas ({empresas.count()} empresas)"
            )

        total_documentos = 0
        documentos_actualizados = 0

        for empresa in empresas:
            self.stdout.write(f"\n🏢 Empresa: {empresa.nombre_taller}")

            # Obtener documentos no pagados de esta empresa
            documentos = Documento.objects.filter(
                empresa=empresa, estado_pago__in=["NO_PAGADO", "PARCIAL"]
            ).select_related("cliente", "vehiculo")

            empresa_total = documentos.count()
            total_documentos += empresa_total

            if empresa_total == 0:
                self.stdout.write("   ✅ Todos los documentos ya están pagados")
                continue

            self.stdout.write(
                f"   📄 Encontrados {empresa_total} documentos no pagados"
            )

            if dry_run:
                # Solo mostrar qué se haría
                for doc in documentos[:5]:  # Mostrar solo los primeros 5 como ejemplo
                    self.stdout.write(
                        f"      - {doc.tipo} #{doc.numero} - {doc.cliente.nombre} - ${doc.total}"
                    )
                if empresa_total > 5:
                    self.stdout.write(f"      ... y {empresa_total - 5} documentos más")
            else:
                # Realizar la actualización
                with transaction.atomic():
                    updated = documentos.update(estado_pago="PAGADO", pagado=True)
                    documentos_actualizados += updated
                    self.stdout.write(
                        f"   ✅ Marcados {updated} documentos como pagados"
                    )

        # Resumen final
        self.stdout.write("\n" + "=" * 50)
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"🔍 MODO SIMULACIÓN: Se marcarían {total_documentos} documentos como pagados"
                )
            )
            self.stdout.write("💡 Para aplicar los cambios, ejecuta sin --dry-run")
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ PROCESO COMPLETADO: {documentos_actualizados} documentos marcados como pagados"
                )
            )
            self.stdout.write(f"📊 Total de documentos procesados: {total_documentos}")

        self.stdout.write(
            self.style.SUCCESS("🎉 ¡Proceso de marcado de documentos completado!")
        )
