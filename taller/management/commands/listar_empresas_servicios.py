"""
Comando para listar empresas y la cantidad de servicios que tienen.

Uso:
    python manage.py listar_empresas_servicios
"""

from django.core.management.base import BaseCommand
from django.db.models import Count

from taller.models import Empresa
from taller.servicios.models import Servicio


class Command(BaseCommand):
    help = 'Lista todas las empresas y la cantidad de servicios que tienen'

    def add_arguments(self, parser):
        parser.add_argument(
            '--min-servicios',
            type=int,
            default=0,
            help='Filtrar empresas con al menos N servicios (default: 0)'
        )

    def handle(self, *args, **options):
        min_servicios = options['min_servicios']
        
        self.stdout.write("Buscando empresas y sus servicios...\n")
        
        # Obtener todas las empresas con el conteo de servicios
        empresas = Empresa.objects.annotate(
            total_servicios=Count('servicio')
        ).order_by('-total_servicios', 'id')
        
        if min_servicios > 0:
            empresas = empresas.filter(total_servicios__gte=min_servicios)
        
        total_empresas = empresas.count()
        
        if total_empresas == 0:
            self.stdout.write(
                self.style.WARNING(
                    f"ADVERTENCIA: No se encontraron empresas con al menos {min_servicios} servicios."
                )
            )
            return
        
        self.stdout.write("=" * 70)
        self.stdout.write(f"{'ID':<5} {'Nombre del Taller':<30} {'Servicios':<10} {'País':<5}")
        self.stdout.write("=" * 70)
        
        for empresa in empresas:
            nombre = empresa.nombre_taller[:28] if len(empresa.nombre_taller) > 28 else empresa.nombre_taller
            servicios_count = empresa.total_servicios
            
            # Color según cantidad de servicios
            if servicios_count == 0:
                style = self.style.WARNING
            elif servicios_count >= 10:
                style = self.style.SUCCESS
            else:
                style = self.style.NOTICE
            
            self.stdout.write(
                style(
                    f"{empresa.id:<5} {nombre:<30} {servicios_count:<10} {empresa.pais:<5}"
                )
            )
        
        self.stdout.write("=" * 70)
        
        # Resumen
        total_servicios = sum(emp.total_servicios for emp in empresas)
        empresas_con_servicios = empresas.filter(total_servicios__gt=0).count()
        
        self.stdout.write(f"\nRESUMEN:")
        self.stdout.write(f"   - Total empresas: {total_empresas}")
        self.stdout.write(f"   - Empresas con servicios: {empresas_con_servicios}")
        self.stdout.write(f"   - Total servicios: {total_servicios}")
        
        # Recomendación de empresa maestra
        empresa_maestra = empresas.filter(total_servicios__gt=0).first()
        if empresa_maestra:
            self.stdout.write(f"\nRECOMENDACION:")
            self.stdout.write(
                self.style.SUCCESS(
                    f"   Empresa ID {empresa_maestra.id} ({empresa_maestra.nombre_taller}) "
                    f"tiene {empresa_maestra.total_servicios} servicios."
                )
            )
            self.stdout.write(
                f"   Puedes usarla como empresa maestra con: --empresa-maestra {empresa_maestra.id}"
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    "\nADVERTENCIA: No hay empresas con servicios. Necesitas crear servicios primero."
                )
            )

