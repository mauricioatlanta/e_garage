"""
Comando para limpiar marcas con nombres que son solo números
Ejecutar: python manage.py limpiar_marcas_numericas
"""

from django.core.management.base import BaseCommand

from taller.models.marca import Marca
from taller.models.modelo import Modelo


class Command(BaseCommand):
    help = "Elimina o corrige marcas con nombres que son solo números (errores de datos)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Solo mostrar qué se haría sin hacer cambios",
        )
        parser.add_argument(
            "--delete",
            action="store_true",
            help="Eliminar marcas problemáticas (solo si no tienen modelos)",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        delete_mode = options["delete"]

        self.stdout.write(self.style.SUCCESS("🔍 Buscando marcas con nombres numéricos...\n"))

        # Buscar marcas con nombres que son solo números
        marcas_problematicas = []
        for marca in Marca.objects.all():
            if marca.nombre and marca.nombre.strip().isdigit():
                modelos_count = marca.modelo_set.count()
                marcas_problematicas.append((marca, modelos_count))

        if not marcas_problematicas:
            self.stdout.write(
                self.style.SUCCESS("✅ No se encontraron marcas con nombres numéricos")
            )
            return

        self.stdout.write(
            self.style.WARNING(
                f"⚠️  Se encontraron {len(marcas_problematicas)} marcas problemáticas:\n"
            )
        )

        for marca, modelos_count in marcas_problematicas:
            self.stdout.write(
                f"   - ID={marca.id}, Nombre='{marca.nombre}', Country='{marca.country}', "
                f"Modelos asociados: {modelos_count}"
            )

        if dry_run:
            self.stdout.write(self.style.WARNING("\n🔍 DRY RUN: No se realizarán cambios"))
            return

        # Procesar marcas problemáticas
        eliminadas = 0
        no_eliminadas = 0

        for marca, modelos_count in marcas_problematicas:
            if modelos_count == 0:
                if delete_mode:
                    marca.delete()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✅ Eliminada: Marca ID {marca.id} (nombre='{marca.nombre}')"
                        )
                    )
                    eliminadas += 1
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f"⚠️  Marca ID {marca.id} puede ser eliminada (no tiene modelos). "
                            f"Usa --delete para eliminarla."
                        )
                    )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"❌ Marca ID {marca.id} NO puede ser eliminada (tiene {modelos_count} modelos asociados)"
                    )
                )
                no_eliminadas += 1

        # Resumen
        self.stdout.write(self.style.SUCCESS("\n🎉 RESUMEN:"))
        if delete_mode:
            self.stdout.write(self.style.SUCCESS(f"✅ Marcas eliminadas: {eliminadas}"))
        else:
            self.stdout.write(
                self.style.WARNING(
                    f"💡 Usa --delete para eliminar {len([m for m, c in marcas_problematicas if c == 0])} marcas sin modelos"
                )
            )
        if no_eliminadas > 0:
            self.stdout.write(
                self.style.WARNING(
                    f"⚠️  Marcas con modelos (no eliminadas): {no_eliminadas}. "
                    f"Revisa manualmente estas marcas."
                )
            )

        # Verificar marcas USA después de la limpieza
        total_usa = Marca.objects.filter(country="US").count()
        self.stdout.write(f"\n🚗 Total marcas USA después de limpieza: {total_usa}")
