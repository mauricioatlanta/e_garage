from django.core.management.base import BaseCommand
from taller.models.ubicacion import Estado, Ciudad
from decimal import Decimal

class Command(BaseCommand):
    help = 'Importa estados y ciudades principales de EE.UU.'

    def handle(self, *args, **options):
        self.stdout.write('🌎 Importando estados y ciudades de EE.UU...')
        
        # Datos de estados con sales tax y timezone
        estados_data = [
            # Estado, Código, Sales Tax (%), Timezone
            ('Georgia', 'GA', Decimal('7.25'), 'America/New_York'),
            ('Florida', 'FL', Decimal('6.00'), 'America/New_York'),
            ('California', 'CA', Decimal('8.25'), 'America/Los_Angeles'),
            ('Texas', 'TX', Decimal('6.25'), 'America/Chicago'),
            ('New York', 'NY', Decimal('8.00'), 'America/New_York'),
            ('Illinois', 'IL', Decimal('6.25'), 'America/Chicago'),
            ('Pennsylvania', 'PA', Decimal('6.00'), 'America/New_York'),
            ('Ohio', 'OH', Decimal('5.75'), 'America/New_York'),
            ('North Carolina', 'NC', Decimal('4.75'), 'America/New_York'),
            ('Michigan', 'MI', Decimal('6.00'), 'America/Detroit'),
            ('New Jersey', 'NJ', Decimal('6.63'), 'America/New_York'),
            ('Virginia', 'VA', Decimal('5.30'), 'America/New_York'),
            ('Washington', 'WA', Decimal('6.50'), 'America/Los_Angeles'),
            ('Arizona', 'AZ', Decimal('5.60'), 'America/Phoenix'),
            ('Massachusetts', 'MA', Decimal('6.25'), 'America/New_York'),
            ('Tennessee', 'TN', Decimal('7.00'), 'America/Chicago'),
            ('Indiana', 'IN', Decimal('7.00'), 'America/Indiana/Indianapolis'),
            ('Missouri', 'MO', Decimal('4.23'), 'America/Chicago'),
            ('Maryland', 'MD', Decimal('6.00'), 'America/New_York'),
            ('Wisconsin', 'WI', Decimal('5.00'), 'America/Chicago'),
            ('Colorado', 'CO', Decimal('2.90'), 'America/Denver'),
            ('Minnesota', 'MN', Decimal('6.88'), 'America/Chicago'),
            ('South Carolina', 'SC', Decimal('6.00'), 'America/New_York'),
            ('Alabama', 'AL', Decimal('4.00'), 'America/Chicago'),
            ('Louisiana', 'LA', Decimal('4.45'), 'America/Chicago'),
        ]

        # Crear estados
        for nombre, codigo, sales_tax, timezone in estados_data:
            estado, created = Estado.objects.get_or_create(
                codigo=codigo,
                defaults={
                    'nombre': nombre,
                    'sales_tax': sales_tax,
                    'timezone': timezone
                }
            )
            if created:
                self.stdout.write(f'✅ Creado estado: {estado}')

        # Ciudades de Georgia (todas las principales)
        georgia = Estado.objects.get(codigo='GA')
        ciudades_georgia = [
            ('Atlanta', 498715, True, Decimal('33.748995'), Decimal('-84.387982')),
            ('Augusta', 197166, False, Decimal('33.471092'), Decimal('-81.975402')),
            ('Columbus', 194058, False, Decimal('32.460976'), Decimal('-84.987747')),
            ('Macon', 153159, False, Decimal('32.840694'), Decimal('-83.632402')),
            ('Savannah', 147780, False, Decimal('32.076174'), Decimal('-81.088371')),
            ('Athens', 127064, False, Decimal('33.960902'), Decimal('-83.377314')),
            ('Sandy Springs', 108080, False, Decimal('33.924869'), Decimal('-84.378581')),
            ('Roswell', 94986, False, Decimal('34.023122'), Decimal('-84.361549')),
            ('Johns Creek', 84551, False, Decimal('34.028762'), Decimal('-84.198578')),
            ('Albany', 72634, False, Decimal('31.578718'), Decimal('-84.155741')),
        ]

        for nombre, poblacion, es_capital, latitud, longitud in ciudades_georgia:
            ciudad, created = Ciudad.objects.get_or_create(
                nombre=nombre,
                estado=georgia,
                defaults={
                    'poblacion': poblacion,
                    'es_capital': es_capital,
                    'latitud': latitud,
                    'longitud': longitud
                }
            )
            if created:
                self.stdout.write(f'✅ Creada ciudad: {ciudad}')

        # 10 ciudades más grandes de estados clave
        ciudades_principales = {
            'FL': [
                ('Jacksonville', 949611, False),
                ('Miami', 442241, False),
                ('Tampa', 384959, False),
                ('Orlando', 307573, False),
                ('St. Petersburg', 265098, False),
                ('Hialeah', 223109, False),
                ('Tallahassee', 194500, True),  # Capital
                ('Fort Lauderdale', 182760, False),
                ('Port St. Lucie', 195248, False),
                ('Cape Coral', 194016, False),
            ],
            'CA': [
                ('Los Angeles', 3898747, False),
                ('San Diego', 1425976, False),
                ('San Jose', 1013240, False),
                ('San Francisco', 873965, False),
                ('Fresno', 542107, False),
                ('Sacramento', 513624, True),  # Capital
                ('Long Beach', 466742, False),
                ('Oakland', 440646, False),
                ('Bakersfield', 380874, False),
                ('Anaheim', 346824, False),
            ],
            'TX': [
                ('Houston', 2304580, False),
                ('San Antonio', 1547253, False),
                ('Dallas', 1343573, False),
                ('Austin', 978908, True),  # Capital
                ('Fort Worth', 918915, False),
                ('El Paso', 695044, False),
                ('Charlotte', 885708, False),
                ('Corpus Christi', 326586, False),
                ('Plano', 285494, False),
                ('Laredo', 260654, False),
            ],
            'NY': [
                ('New York City', 8336817, False),
                ('Buffalo', 255284, False),
                ('Rochester', 206284, False),
                ('Yonkers', 211569, False),
                ('Syracuse', 144142, False),
                ('Albany', 97279, True),  # Capital
                ('New Rochelle', 79726, False),
                ('Mount Vernon', 67292, False),
                ('Schenectady', 65273, False),
                ('Utica', 59984, False),
            ]
        }

        for codigo_estado, ciudades in ciudades_principales.items():
            try:
                estado = Estado.objects.get(codigo=codigo_estado)
                for nombre, poblacion, es_capital in ciudades:
                    ciudad, created = Ciudad.objects.get_or_create(
                        nombre=nombre,
                        estado=estado,
                        defaults={
                            'poblacion': poblacion,
                            'es_capital': es_capital,
                        }
                    )
                    if created:
                        self.stdout.write(f'✅ Creada ciudad: {ciudad}')
            except Estado.DoesNotExist:
                self.stdout.write(f'❌ Estado {codigo_estado} no encontrado')

        self.stdout.write(
            self.style.SUCCESS(
                f'🎉 Importación completada!\n'
                f'Estados: {Estado.objects.count()}\n'
                f'Ciudades: {Ciudad.objects.count()}'
            )
        )
