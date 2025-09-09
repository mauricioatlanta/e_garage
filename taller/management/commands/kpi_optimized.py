from django.core.management.base import BaseCommand
from taller.utils.kpi_helpers import KPICalculator, get_kpi_tecnico_mes_actual, get_kpi_servicio_mes_actual


class Command(BaseCommand):
    help = "KPIs optimizados usando patrones ORM eficientes"

    def add_arguments(self, parser):
        parser.add_argument(
            '--empresa',
            type=int,
            help='ID de la empresa para filtrar KPIs',
        )
        parser.add_argument(
            '--meses',
            type=int,
            default=12,
            help='Número de meses para rendimiento mensual',
        )

    def handle(self, *args, **options):
        empresa_id = options.get('empresa')
        meses = options.get('meses')
        
        self.stdout.write("📊 Ejecutando KPIs optimizados...")
        
        try:
            # Inicializar calculadora
            calculator = KPICalculator(empresa_id)
            
            # KPI 1: Técnicos del mes actual
            self.stdout.write("\n1. Técnicos del mes actual:")
            tecnicos = get_kpi_tecnico_mes_actual(empresa_id)
            for tecnico in tecnicos:
                self.stdout.write(
                    f"   - {tecnico['documento__tecnico_responsable__nombre']}: "
                    f"${tecnico['total']} ({tecnico['cantidad_documentos']} docs)"
                )
            
            # KPI 2: Servicios del mes actual
            self.stdout.write("\n2. Servicios del mes actual:")
            servicios = get_kpi_servicio_mes_actual(empresa_id)
            for servicio in servicios:
                self.stdout.write(
                    f"   - {servicio['servicio__nombre']}: "
                    f"${servicio['total']} ({servicio['cantidad_veces']} veces)"
                )
            
            # KPI 3: Documentos por estado
            self.stdout.write("\n3. Documentos por estado:")
            estados = calculator.get_documentos_por_estado()
            for estado in estados:
                self.stdout.write(
                    f"   - {estado['estado']}: "
                    f"{estado['cantidad']} documentos (${estado['total_monto']})"
                )
            
            # KPI 4: Técnicos más activos
            self.stdout.write("\n4. Técnicos más activos:")
            tecnicos_activos = calculator.get_tecnicos_mas_activos()
            for tecnico in tecnicos_activos:
                self.stdout.write(
                    f"   - {tecnico.nombre}: "
                    f"{tecnico.cantidad_documentos} documentos"
                )
            
            # KPI 5: Rendimiento mensual
            self.stdout.write(f"\n5. Rendimiento mensual (últimos {meses} meses):")
            rendimiento = calculator.get_rendimiento_mensual(meses)
            for mes in rendimiento:
                self.stdout.write(
                    f"   - {mes['mes'].strftime('%Y-%m')}: "
                    f"${mes['total']} ({mes['cantidad_documentos']} docs)"
                )
            
            # KPI 6: Clientes más activos
            self.stdout.write("\n6. Clientes más activos:")
            clientes = calculator.get_clientes_mas_activos()
            for cliente in clientes:
                self.stdout.write(
                    f"   - {cliente.nombre}: "
                    f"{cliente.cantidad_documentos} documentos (${cliente.total_monto})"
                )
            
            # KPI 7: Vehículos más serviciados
            self.stdout.write("\n7. Vehículos más serviciados:")
            vehiculos = calculator.get_vehiculos_mas_serviciados()
            for vehiculo in vehiculos:
                self.stdout.write(
                    f"   - {vehiculo.marca} {vehiculo.modelo} ({vehiculo.patente}): "
                    f"{vehiculo.cantidad_documentos} servicios (${vehiculo.total_monto})"
                )
            
            self.stdout.write(
                self.style.SUCCESS("\n✅ KPIs optimizados completados")
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error en KPIs optimizados: {e}")
            )
            raise
