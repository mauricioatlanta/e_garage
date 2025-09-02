"""
Management command simplificado para auditar el aislamiento multi-tenant
"""

from django.core.management.base import BaseCommand
from django.db.models import Q, F

class Command(BaseCommand):
    help = 'Audita el aislamiento multi-tenant'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Solo mostrar problemas sin corregir'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write(
            self.style.SUCCESS(
                f'=== AUDITORÍA MULTI-TENANT {"(SOLO LECTURA)" if dry_run else "(MODO CORRECCIÓN)"} ==='
            )
        )

        try:
            # Auditar clientes
            self.audit_clientes()
            
            # Auditar vehículos  
            self.audit_vehiculos()
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error durante auditoría: {e}')
            )
            return

        self.stdout.write(
            self.style.SUCCESS('=== AUDITORÍA COMPLETADA ===')
        )

    def audit_clientes(self):
        """Auditar clientes sin empresa"""
        from taller.models.clientes import Cliente
        
        self.stdout.write('\n--- AUDITANDO CLIENTES ---')
        
        # Clientes sin empresa
        bad_clientes = Cliente.objects.filter(empresa__isnull=True)
        count = bad_clientes.count()
        
        if count > 0:
            self.stdout.write(
                self.style.ERROR(f'❌ {count} clientes sin empresa asignada')
            )
            for cliente in bad_clientes[:5]:  # Mostrar primeros 5
                self.stdout.write(f'  - Cliente ID: {cliente.pk}, Nombre: {cliente.nombre}')
        else:
            self.stdout.write(self.style.SUCCESS('✅ Todos los clientes tienen empresa'))

    def audit_vehiculos(self):
        """Auditar vehículos con empresas inconsistentes"""
        from taller.models.vehiculos import Vehiculo
        
        self.stdout.write('\n--- AUDITANDO VEHÍCULOS ---')
        
        # Vehículos sin empresa
        bad_vehiculos = Vehiculo.objects.filter(empresa__isnull=True)
        count = bad_vehiculos.count()
        
        if count > 0:
            self.stdout.write(
                self.style.ERROR(f'❌ {count} vehículos sin empresa')
            )
            for vehiculo in bad_vehiculos[:5]:
                self.stdout.write(f'  - Vehículo ID: {vehiculo.pk}, Patente: {vehiculo.patente}')
        else:
            self.stdout.write(self.style.SUCCESS('✅ Todos los vehículos tienen empresa'))

        # Vehículos con empresa diferente a su cliente
        try:
            inconsistent_vehiculos = Vehiculo.objects.filter(
                ~Q(empresa=F('cliente__empresa'))
            ).exclude(cliente__empresa__isnull=True)
            
            count = inconsistent_vehiculos.count()
            if count > 0:
                self.stdout.write(
                    self.style.ERROR(f'❌ {count} vehículos con empresa inconsistente con su cliente')
                )
                for vehiculo in inconsistent_vehiculos[:5]:
                    self.stdout.write(f'  - Vehículo ID: {vehiculo.pk}')
            else:
                self.stdout.write(self.style.SUCCESS('✅ Vehículos tienen empresa consistente'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'⚠️ No se pudo verificar consistencia: {e}'))
