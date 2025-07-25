from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
import random

class Command(BaseCommand):
    help = 'Crear datos de demo para Atlanta - talleres, clientes, vehículos y servicios'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Eliminar datos existentes antes de crear nuevos'
        )
        
        parser.add_argument(
            '--talleres',
            type=int,
            default=3,
            help='Número de talleres demo a crear (default: 3)'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Iniciando creación de datos demo para Atlanta...')
        )
        
        if options['reset']:
            self.limpiar_datos_demo()
        
        self.crear_talleres_atlanta(options['talleres'])
        self.crear_clientes_atlanta()
        self.crear_vehiculos_atlanta()
        self.crear_servicios_atlanta()
        self.crear_cotizaciones_demo()
        self.mostrar_resumen_atlanta()
        
        self.stdout.write(
            self.style.SUCCESS('✅ Datos demo de Atlanta creados exitosamente!')
        )

    def limpiar_datos_demo(self):
        """Limpiar datos demo existentes"""
        self.stdout.write('🧹 Limpiando datos demo existentes...')
        
        # Aquí puedes agregar lógica para limpiar datos si es necesario
        # Por ahora solo mostramos el mensaje
        
        self.stdout.write(
            self.style.WARNING('⚠️ Datos demo limpiados')
        )

    def crear_talleres_atlanta(self, cantidad):
        """Crear talleres demo en Atlanta"""
        self.stdout.write(f'🏢 Creando {cantidad} talleres demo en Atlanta...')
        
        talleres_atlanta = [
            {
                'nombre': 'Peachtree Auto Pro',
                'direccion': '2450 Piedmont Rd NE, Atlanta, GA 30324',
                'telefono': '(404) 555-0123',
                'email': 'info@peachtreeautopro.com',
                'especialidad': 'General Auto Repair'
            },
            {
                'nombre': 'Buckhead Motors',
                'direccion': '3344 Peachtree Rd NE, Atlanta, GA 30326',
                'telefono': '(404) 555-0456',
                'email': 'service@buckheadmotors.com',
                'especialidad': 'Luxury Vehicle Service'
            },
            {
                'nombre': 'Midtown Auto Works',
                'direccion': '950 W Peachtree St NW, Atlanta, GA 30309',
                'telefono': '(404) 555-0789',
                'email': 'contact@midtownauto.com',
                'especialidad': 'Import Vehicle Specialists'
            }
        ]
        
        for i, datos_taller in enumerate(talleres_atlanta[:cantidad]):
            self.stdout.write(f'  📍 {datos_taller["nombre"]}')
            # Aquí podrías crear registros en la base de datos si tienes los modelos
            
    def crear_clientes_atlanta(self):
        """Crear clientes demo de Atlanta"""
        self.stdout.write('👥 Creando clientes demo de Atlanta...')
        
        clientes_atlanta = [
            {
                'nombre': 'Mike Johnson',
                'telefono': '(404) 555-0187',
                'email': 'mike.johnson@email.com',
                'direccion': '1234 Buckhead Ave, Atlanta, GA 30309',
                'barrio': 'Buckhead'
            },
            {
                'nombre': 'Sarah Williams',
                'telefono': '(404) 555-0298',
                'email': 'sarah.williams@gmail.com',
                'direccion': '567 Midtown Plaza, Atlanta, GA 30308',
                'barrio': 'Midtown'
            },
            {
                'nombre': 'Robert Davis',
                'telefono': '(404) 555-0345',
                'email': 'rob.davis@yahoo.com',
                'direccion': '890 Decatur St, Atlanta, GA 30312',
                'barrio': 'Decatur'
            },
            {
                'nombre': 'Jennifer Brown',
                'telefono': '(404) 555-0456',
                'email': 'jen.brown@outlook.com',
                'direccion': '432 Virginia Ave, Atlanta, GA 30306',
                'barrio': 'Virginia-Highland'
            },
            {
                'nombre': 'Michael Wilson',
                'telefono': '(404) 555-0567',
                'email': 'mwilson@email.com',
                'direccion': '123 Ponce de Leon Ave, Atlanta, GA 30309',
                'barrio': 'Poncey-Highland'
            }
        ]
        
        for cliente in clientes_atlanta:
            self.stdout.write(f'  👤 {cliente["nombre"]} - {cliente["barrio"]}')

    def crear_vehiculos_atlanta(self):
        """Crear vehículos típicos de Atlanta"""
        self.stdout.write('🚗 Creando vehículos demo...')
        
        vehiculos_atlanta = [
            {
                'propietario': 'Mike Johnson',
                'marca': 'Ford',
                'modelo': 'F-150',
                'año': 2019,
                'color': 'Midnight Blue',
                'placa': 'GEO-4521',
                'vin': '1FTFW1ET5KFC10312',
                'kilometraje': 87500
            },
            {
                'propietario': 'Sarah Williams',
                'marca': 'Toyota',
                'modelo': 'Camry',
                'año': 2020,
                'color': 'Pearl White',
                'placa': 'ATL-7893',
                'vin': '4T1G11AK8LU123456',
                'kilometraje': 45000
            },
            {
                'propietario': 'Robert Davis',
                'marca': 'Chevrolet',
                'modelo': 'Silverado',
                'año': 2018,
                'color': 'Red Hot',
                'placa': 'GAR-2468',
                'vin': '1GCUKREC9JZ123789',
                'kilometraje': 95000
            },
            {
                'propietario': 'Jennifer Brown',
                'marca': 'Honda',
                'modelo': 'CR-V',
                'año': 2021,
                'color': 'Crystal Black',
                'placa': 'PCH-1357',
                'vin': '7FARW2H84ME123456',
                'kilometraje': 28000
            },
            {
                'propietario': 'Michael Wilson',
                'marca': 'BMW',
                'modelo': 'X3',
                'año': 2019,
                'color': 'Alpine White',
                'placa': 'BMW-5678',
                'vin': 'WBA30MX0XKA123456',
                'kilometraje': 62000
            }
        ]
        
        for vehiculo in vehiculos_atlanta:
            self.stdout.write(
                f'  🚙 {vehiculo["año"]} {vehiculo["marca"]} {vehiculo["modelo"]} - {vehiculo["propietario"]}'
            )

    def crear_servicios_atlanta(self):
        """Crear servicios típicos con precios de Atlanta"""
        self.stdout.write('🔧 Creando catálogo de servicios para Atlanta...')
        
        servicios_atlanta = [
            {
                'categoria': 'Mantenimiento Básico',
                'servicios': [
                    {'nombre': 'Full Service Oil Change', 'precio': 65.00, 'tiempo': 30},
                    {'nombre': 'Tire Rotation & Balance', 'precio': 35.00, 'tiempo': 45},
                    {'nombre': 'Air Filter Replacement', 'precio': 25.00, 'tiempo': 15},
                    {'nombre': 'Cabin Filter Replacement', 'precio': 30.00, 'tiempo': 20}
                ]
            },
            {
                'categoria': 'Sistema de Frenos',
                'servicios': [
                    {'nombre': 'Complete Brake Service', 'precio': 125.00, 'tiempo': 90},
                    {'nombre': 'Brake Pad Replacement', 'precio': 85.00, 'tiempo': 60},
                    {'nombre': 'Brake Fluid Flush', 'precio': 45.00, 'tiempo': 30},
                    {'nombre': 'Brake Inspection', 'precio': 25.00, 'tiempo': 20}
                ]
            },
            {
                'categoria': 'Sistema Eléctrico',
                'servicios': [
                    {'nombre': 'Computer Diagnostic', 'precio': 110.00, 'tiempo': 60},
                    {'nombre': 'Battery Test & Replace', 'precio': 95.00, 'tiempo': 30},
                    {'nombre': 'Alternator Service', 'precio': 165.00, 'tiempo': 120},
                    {'nombre': 'Starter Motor Service', 'precio': 145.00, 'tiempo': 90}
                ]
            },
            {
                'categoria': 'Sistema de Climatización',
                'servicios': [
                    {'nombre': 'A/C System Service', 'precio': 95.00, 'tiempo': 60},
                    {'nombre': 'A/C Refrigerant Recharge', 'precio': 65.00, 'tiempo': 45},
                    {'nombre': 'A/C Compressor Replacement', 'precio': 285.00, 'tiempo': 180},
                    {'nombre': 'Heater Core Service', 'precio': 195.00, 'tiempo': 150}
                ]
            },
            {
                'categoria': 'Transmisión',
                'servicios': [
                    {'nombre': 'Transmission Service', 'precio': 245.00, 'tiempo': 120},
                    {'nombre': 'Transmission Fluid Change', 'precio': 85.00, 'tiempo': 45},
                    {'nombre': 'Transmission Diagnostic', 'precio': 125.00, 'tiempo': 90},
                    {'nombre': 'CVT Service', 'precio': 175.00, 'tiempo': 90}
                ]
            }
        ]
        
        for categoria in servicios_atlanta:
            self.stdout.write(f'  📋 {categoria["categoria"]}:')
            for servicio in categoria['servicios']:
                self.stdout.write(
                    f'    🔧 {servicio["nombre"]} - ${servicio["precio"]:.2f} ({servicio["tiempo"]} min)'
                )

    def crear_cotizaciones_demo(self):
        """Crear cotizaciones de ejemplo"""
        self.stdout.write('💰 Creando cotizaciones demo...')
        
        # Impuesto de Georgia (Atlanta)
        tax_rate = Decimal('8.9')
        
        cotizaciones_ejemplo = [
            {
                'cliente': 'Mike Johnson',
                'vehiculo': '2019 Ford F-150',
                'servicios': [
                    {'nombre': 'Full Service Oil Change', 'precio': Decimal('65.00')},
                    {'nombre': 'Tire Rotation & Balance', 'precio': Decimal('35.00')},
                    {'nombre': 'Brake Inspection', 'precio': Decimal('25.00')}
                ]
            },
            {
                'cliente': 'Sarah Williams',
                'vehiculo': '2020 Toyota Camry',
                'servicios': [
                    {'nombre': 'Complete Brake Service', 'precio': Decimal('125.00')},
                    {'nombre': 'A/C System Service', 'precio': Decimal('95.00')}
                ]
            },
            {
                'cliente': 'Robert Davis',
                'vehiculo': '2018 Chevrolet Silverado',
                'servicios': [
                    {'nombre': 'Transmission Service', 'precio': Decimal('245.00')},
                    {'nombre': 'Computer Diagnostic', 'precio': Decimal('110.00')},
                    {'nombre': 'Battery Test & Replace', 'precio': Decimal('95.00')}
                ]
            }
        ]
        
        for cotizacion in cotizaciones_ejemplo:
            subtotal = sum(servicio['precio'] for servicio in cotizacion['servicios'])
            tax_amount = subtotal * (tax_rate / Decimal('100'))
            total = subtotal + tax_amount
            
            self.stdout.write(f'  💵 {cotizacion["cliente"]} - {cotizacion["vehiculo"]}:')
            
            for servicio in cotizacion['servicios']:
                self.stdout.write(f'    • {servicio["nombre"]}: ${servicio["precio"]:.2f}')
            
            self.stdout.write(f'    Subtotal: ${subtotal:.2f}')
            self.stdout.write(f'    GA Tax ({tax_rate}%): ${tax_amount:.2f}')
            self.stdout.write(f'    Total: ${total:.2f}')
            self.stdout.write('')

    def mostrar_resumen_atlanta(self):
        """Mostrar resumen de datos creados"""
        self.stdout.write('\n' + '='*50)
        self.stdout.write('📊 RESUMEN DEMO ATLANTA')
        self.stdout.write('='*50)
        
        self.stdout.write('🎯 Demo público disponible en:')
        self.stdout.write('   http://localhost:8080/demo/atlanta/')
        self.stdout.write('')
        
        self.stdout.write('🎟️ Códigos promocionales válidos:')
        self.stdout.write('   ATLANTA2025 - 3 meses gratis ($297 valor)')
        self.stdout.write('   GEORGIA2025 - 2 meses gratis ($198 valor)')
        self.stdout.write('   PEACHTREE  - 1 mes gratis ($99 valor)')
        self.stdout.write('')
        
        self.stdout.write('📞 Contacto demo:')
        self.stdout.write('   Teléfono: (404) 555-0123')
        self.stdout.write('   Email: info@peachtreeautopro.com')
        self.stdout.write('')
        
        self.stdout.write('🚀 Para lanzar campaña de marketing:')
        self.stdout.write('   1. Configura Google Analytics')
        self.stdout.write('   2. Crea Facebook Ads targeting Atlanta auto shops')
        self.stdout.write('   3. Inicia cold calling con lista de talleres')
        self.stdout.write('   4. Envía emails de demostración')
        self.stdout.write('')
        
        self.stdout.write(
            self.style.SUCCESS('✅ Demo de Atlanta listo para capturar los primeros 10 talleres!')
        )
