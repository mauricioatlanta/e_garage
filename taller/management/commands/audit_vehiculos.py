from django.core.management.base import BaseCommand
from django.db.models import F
from taller.models.clientes import Cliente
from taller.models.vehiculos import Vehiculo


class Command(BaseCommand):
    help = "Audita coherencia Cliente/Vehículo/Empresa y muestra inconsistencias"

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Corregir inconsistencias automáticamente (basado en cliente.empresa)',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Mostrar información detallada de todos los vehículos',
        )

    def handle(self, *args, **options):
        fix_mode = options['fix']
        verbose = options['verbose']
        
        self.stdout.write("🔍 AUDITORÍA DE COHERENCIA CLIENTE/VEHÍCULO/EMPRESA")
        self.stdout.write("=" * 60)
        
        inconsistentes = []
        vehiculos_procesados = 0
        
        # Obtener todos los vehículos con sus relaciones
        vehiculos = Vehiculo.objects.select_related("cliente", "empresa", "cliente__empresa")
        
        for v in vehiculos:
            vehiculos_procesados += 1
            
            if verbose:
                self.stdout.write(f"\n🚗 Vehículo {v.id}: {v.patente or v.vin or 'Sin patente/VIN'}")
                self.stdout.write(f"   Cliente: {v.cliente} (ID: {v.cliente_id})" if v.cliente else "   Cliente: Sin asignar")
                self.stdout.write(f"   Empresa vehículo: {v.empresa} (ID: {v.empresa_id})")
                if v.cliente:
                    self.stdout.write(f"   Empresa cliente: {v.cliente.empresa} (ID: {v.cliente.empresa_id})")
            
            # Vehículo sin cliente
            if not v.cliente:
                msg = f"Vehículo {v.id} sin cliente asignado (empresa={v.empresa_id})"
                inconsistentes.append({
                    'vehiculo': v,
                    'tipo': 'sin_cliente',
                    'mensaje': msg
                })
                continue
            
            # Empresa del vehículo distinta de la del cliente
            if v.cliente.empresa_id != v.empresa_id:
                msg = (f"Vehículo {v.id} ({v.patente or v.vin or 'Sin patente/VIN'}) → "
                      f"cliente {v.cliente_id} (empresa {v.cliente.empresa_id}) "
                      f"≠ empresa del vehículo {v.empresa_id}")
                inconsistentes.append({
                    'vehiculo': v,
                    'tipo': 'empresa_inconsistente',
                    'mensaje': msg
                })
        
        # Mostrar resumen
        self.stdout.write(f"\n📊 RESUMEN:")
        self.stdout.write(f"   Vehículos procesados: {vehiculos_procesados}")
        self.stdout.write(f"   Inconsistencias encontradas: {len(inconsistentes)}")
        
        if inconsistentes:
            self.stdout.write(self.style.WARNING(f"\n⚠️ INCONSISTENCIAS DETECTADAS ({len(inconsistentes)}):"))
            
            # Agrupar por tipo
            sin_cliente = [i for i in inconsistentes if i['tipo'] == 'sin_cliente']
            empresa_inconsistente = [i for i in inconsistentes if i['tipo'] == 'empresa_inconsistente']
            
            if sin_cliente:
                self.stdout.write(self.style.ERROR(f"\n🚫 Vehículos sin cliente asignado ({len(sin_cliente)}):"))
                for item in sin_cliente:
                    self.stdout.write(f"   - {item['mensaje']}")
            
            if empresa_inconsistente:
                self.stdout.write(self.style.ERROR(f"\n🔄 Empresa inconsistente ({len(empresa_inconsistente)}):"))
                for item in empresa_inconsistente:
                    self.stdout.write(f"   - {item['mensaje']}")
            
            # Modo de corrección
            if fix_mode:
                self.stdout.write(self.style.WARNING(f"\n🔧 MODO CORRECCIÓN ACTIVADO"))
                self.corregir_inconsistencias(inconsistentes)
            else:
                self.stdout.write(f"\n💡 Para corregir automáticamente, ejecuta:")
                self.stdout.write(f"   python manage.py audit_vehiculos --fix")
                
        else:
            self.stdout.write(self.style.SUCCESS(f"\n✅ NO SE ENCONTRARON INCONSISTENCIAS"))
            self.stdout.write("   Todos los vehículos están correctamente alineados con sus clientes y empresas.")
        
        # Estadísticas adicionales
        self.mostrar_estadisticas()

    def corregir_inconsistencias(self, inconsistentes):
        """Corrige las inconsistencias encontradas"""
        corregidos = 0
        
        for item in inconsistentes:
            v = item['vehiculo']
            
            if item['tipo'] == 'sin_cliente':
                self.stdout.write(f"   ⚠️ Vehículo {v.id} sin cliente - requiere intervención manual")
                continue
            
            elif item['tipo'] == 'empresa_inconsistente':
                if v.cliente and v.cliente.empresa:
                    empresa_original = v.empresa
                    v.empresa = v.cliente.empresa
                    v.save()
                    self.stdout.write(f"   ✅ Vehículo {v.id}: {empresa_original} → {v.cliente.empresa}")
                    corregidos += 1
        
        if corregidos > 0:
            self.stdout.write(self.style.SUCCESS(f"\n🎉 CORRECCIÓN COMPLETADA: {corregidos} vehículos corregidos"))
        else:
            self.stdout.write(f"\nℹ️ No se pudieron corregir inconsistencias automáticamente")

    def mostrar_estadisticas(self):
        """Muestra estadísticas adicionales"""
        self.stdout.write(f"\n📈 ESTADÍSTICAS ADICIONALES:")
        
        # Vehículos por país
        for pais in ['CL', 'US']:
            vehiculos_pais = Vehiculo.objects.filter(empresa__pais=pais).count()
            self.stdout.write(f"   {pais}: {vehiculos_pais} vehículos")
        
        # Vehículos sin cliente
        sin_cliente = Vehiculo.objects.filter(cliente__isnull=True).count()
        if sin_cliente > 0:
            self.stdout.write(f"   Vehículos sin cliente: {sin_cliente}")
        
        # Vehículos con empresa inconsistente (usando F)
        try:
            inconsistentes_count = Vehiculo.objects.exclude(empresa=F('cliente__empresa')).count()
            if inconsistentes_count > 0:
                self.stdout.write(f"   Vehículos con empresa inconsistente: {inconsistentes_count}")
        except Exception as e:
            self.stdout.write(f"   Error calculando inconsistencias: {e}")
