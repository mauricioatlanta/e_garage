"""
Management command para crear traducciones en español para servicios que solo tienen nombres en inglés.
"""

from django.core.management.base import BaseCommand
from django.db.models import Q

from taller.servicios.models import Servicio, ServicioName


class Command(BaseCommand):
    help = "Crea traducciones en español para servicios que solo tienen nombres en inglés"

    # Diccionario completo de traducciones inglés -> español chileno
    TRADUCCIONES = {
        # Engine Services
        "Engine Rebuild": "Reparación Completa de Motor",
        "Head Gasket Replacement": "Cambio de Junta de Culata",
        "Timing Belt/Chain Service": "Servicio de Correa/Cadena de Distribución",
        "Valve Adjustment": "Regulación de Válvulas",
        "Engine Mount Replacement": "Cambio de Soporte de Motor",
        "Cylinder Head Repair": "Reparación de Culata",
        "Engine Overhaul": "Reconstrucción de Motor",
        "Engine Replacement": "Reemplazo de Motor",
        "Crankshaft Repair": "Reparación de Cigüeñal",
        "Piston Ring Replacement": "Cambio de Anillos de Pistón",
        "Camshaft Replacement": "Cambio de Árbol de Levas",
        "Valve Replacement": "Cambio de Válvulas",
        "Engine Seals Replacement": "Cambio de Retenes de Motor",
        "Engine Gasket Replacement": "Cambio de Juntas de Motor",
        # Oil Change Services
        "Conventional Oil Change": "Cambio de Aceite Convencional",
        "Synthetic Oil Change": "Cambio de Aceite Sintético",
        "High Mileage Oil Change": "Cambio de Aceite para Alto Kilometraje",
        "Oil Change with Filter": "Cambio de Aceite con Filtro",
        "Oil Change": "Cambio de Aceite",
        "Full Synthetic Oil Change": "Cambio de Aceite 100% Sintético",
        "Semi-Synthetic Oil Change": "Cambio de Aceite Semi-Sintético",
        # Filter Services
        "Air Filter Replacement": "Cambio de Filtro de Aire",
        "Cabin Air Filter Replacement": "Cambio de Filtro de Aire de Habitáculo",
        "Fuel Filter Replacement": "Cambio de Filtro de Combustible",
        "Oil Filter Replacement": "Cambio de Filtro de Aceite",
        "Transmission Filter Replacement": "Cambio de Filtro de Transmisión",
        # Belt Services
        "Serpentine Belt Replacement": "Cambio de Correa de Accesorios",
        "Timing Belt Replacement": "Cambio de Correa de Distribución",
        "Accessory Belt Replacement": "Cambio de Correa de Accesorios",
        "Drive Belt Replacement": "Cambio de Correa de Transmisión",
        "V-Belt Replacement": "Cambio de Correa en V",
        # Fluid Services
        "Transmission Fluid Service": "Servicio de Fluido de Transmisión",
        "Brake Fluid Service": "Servicio de Líquido de Frenos",
        "Power Steering Fluid Service": "Servicio de Líquido de Dirección",
        "Coolant Flush": "Lavado de Radiador",
        "Coolant Replacement": "Cambio de Refrigerante",
        "Power Steering Flush": "Lavado de Sistema de Dirección",
        "Brake Fluid Flush": "Lavado de Sistema de Frenos",
        "Transmission Flush": "Lavado de Transmisión",
        "Differential Fluid Service": "Servicio de Fluido de Diferencial",
        # Brake Services
        "Brake Pad Replacement": "Cambio de Pastillas de Freno",
        "Brake Rotor Replacement": "Cambio de Discos de Freno",
        "Brake Caliper Replacement": "Cambio de Pinzas de Freno",
        "Brake Line Replacement": "Cambio de Líneas de Freno",
        "Brake Fluid Replacement": "Cambio de Líquido de Frenos",
        "Brake Service": "Servicio de Frenos",
        "Brake Inspection": "Revisión de Frenos",
        "Brake System Repair": "Reparación de Sistema de Frenos",
        # Suspension Services
        "Shock Absorber Replacement": "Cambio de Amortiguadores",
        "Strut Replacement": "Cambio de Montantes",
        "Spring Replacement": "Cambio de Resortes",
        "Suspension Repair": "Reparación de Suspensión",
        "Wheel Bearing Replacement": "Cambio de Rodamientos de Rueda",
        "Ball Joint Replacement": "Cambio de Terminales de Dirección",
        "Tie Rod Replacement": "Cambio de Barras de Dirección",
        "Control Arm Replacement": "Cambio de Brazos de Control",
        "Sway Bar Replacement": "Cambio de Barra Estabilizadora",
        "Bushing Replacement": "Cambio de Bujes",
        # Transmission Services
        "Transmission Repair": "Reparación de Transmisión",
        "Transmission Rebuild": "Reconstrucción de Transmisión",
        "Transmission Replacement": "Reemplazo de Transmisión",
        "Clutch Replacement": "Cambio de Embrague",
        "Clutch Repair": "Reparación de Embrague",
        "Transmission Service": "Servicio de Transmisión",
        # Electrical Services
        "Battery Replacement": "Cambio de Batería",
        "Alternator Replacement": "Cambio de Alternador",
        "Starter Replacement": "Cambio de Motor de Arranque",
        "Battery Service": "Servicio de Batería",
        "Electrical System Repair": "Reparación de Sistema Eléctrico",
        "Fuse Replacement": "Cambio de Fusibles",
        "Wiring Repair": "Reparación de Cableado",
        # Cooling System Services
        "Radiator Repair": "Reparación de Radiador",
        "Radiator Replacement": "Cambio de Radiador",
        "Water Pump Replacement": "Cambio de Bomba de Agua",
        "Thermostat Replacement": "Cambio de Termostato",
        "Radiator Hose Replacement": "Cambio de Mangueras de Radiador",
        "Cooling System Service": "Servicio de Sistema de Refrigeración",
        # Exhaust System Services
        "Exhaust System Repair": "Reparación de Sistema de Escape",
        "Muffler Replacement": "Cambio de Silenciador",
        "Catalytic Converter Replacement": "Cambio de Convertidor Catalítico",
        "Exhaust Pipe Replacement": "Cambio de Caño de Escape",
        # Air Conditioning Services
        "AC Service": "Servicio de Aire Acondicionado",
        "AC Recharge": "Recarga de Aire Acondicionado",
        "AC Repair": "Reparación de Aire Acondicionado",
        "AC Compressor Replacement": "Cambio de Compresor de A/C",
        "AC Condenser Replacement": "Cambio de Condensador de A/C",
        "AC Evaporator Replacement": "Cambio de Evaporador de A/C",
        # Alignment & Balancing
        "Wheel Alignment": "Alineación de Ruedas",
        "Wheel Balancing": "Balanceo de Ruedas",
        "Tire Rotation": "Rotación de Neumáticos",
        "Tire Replacement": "Cambio de Neumáticos",
        # Diagnostics
        "Engine Diagnostics": "Diagnóstico de Motor",
        "Computer Diagnostics": "Diagnóstico Computarizado",
        "OBD-II Scan": "Escaneo OBD-II",
        "Check Engine Light": "Revisión de Luz de Motor",
        # Maintenance
        "Tune-Up": "Afinamiento",
        "Preventive Maintenance": "Mantenimiento Preventivo",
        "Scheduled Maintenance": "Mantenimiento Programado",
        "Multi-Point Inspection": "Revisión Multipunto",
        # Other Services
        "Spark Plug Replacement": "Cambio de Bujías",
        "Ignition Coil Replacement": "Cambio de Bobinas de Encendido",
        "Fuel Pump Replacement": "Cambio de Bomba de Combustible",
        "Fuel Injector Service": "Servicio de Inyectores",
        "Throttle Body Service": "Servicio de Cuerpo de Acelerador",
        "PCV Valve Replacement": "Cambio de Válvula PCV",
        "EGR Valve Replacement": "Cambio de Válvula EGR",
        "Mass Air Flow Sensor Replacement": "Cambio de Sensor MAF",
        "Oxygen Sensor Replacement": "Cambio de Sensor de Oxígeno",
        "Windscreen Wiper Replacement": "Cambio de Plumillas",
        "Windshield Wiper Replacement": "Cambio de Plumillas",
        "Headlight Replacement": "Cambio de Faros",
        "Taillight Replacement": "Cambio de Luces Traseras",
        "Turn Signal Replacement": "Cambio de Intermitentes",
        # Battery Services
        "Battery Installation": "Instalación de Batería",
        "Battery Testing": "Prueba de Batería",
        "Battery Jump Start": "Arranque con Cables",
        "Battery Terminal Cleaning": "Limpieza de Terminales de Batería",
        # Alternator Services
        "Alternator Repair": "Reparación de Alternador",
        "Alternator Belt Replacement": "Cambio de Correa de Alternador",
        # Starter Services
        "Starter Repair": "Reparación de Motor de Arranque",
        "Starter Solenoid Replacement": "Cambio de Solenoide de Arranque",
        # Tire Services
        "New Tire Installation": "Instalación de Neumáticos Nuevos",
        "Seasonal Tire Change": "Cambio de Neumáticos Estacionales",
        "Run Flat Tire Installation": "Instalación de Neumáticos Run Flat",
        "Tire Mounting & Balancing": "Montaje y Balanceo de Neumáticos",
        "Tire Puncture Repair": "Reparación de Pinchazo",
        "Tire Sidewall Repair": "Reparación de Pared Lateral",
        "Tire Valve Replacement": "Cambio de Válvula de Neumático",
        "Tire Rotation with Inspection": "Rotación de Neumáticos con Inspección",
        "Road Force Balancing": "Balanceo de Fuerza",
        "Front Wheel Alignment": "Alineación delantera",
        "Rear Wheel Alignment": "Alineación trasera",
        "Four Wheel Alignment": "Alineación en Cuatro Ruedas",
        # Additional Services
        "Oil Change Service": "Servicio de Cambio de Aceite",
        "Full Service": "Servicio Completo",
        "Basic Service": "Servicio Básico",
        "Premium Service": "Servicio Premium",
        "Express Service": "Servicio Express",
        "Maintenance Service": "Servicio de Mantenimiento",
        "Inspection Service": "Servicio de Inspección",
        "Diagnostic Service": "Servicio de Diagnóstico",
        # Brake Services (additional)
        "Front Brake Pad Replacement": "Cambio de Pastillas de Freno Delanteras",
        "Rear Brake Pad Replacement": "Cambio de Pastillas de Freno Traseras",
        "Brake Pad & Rotor Service": "Servicio de Pastillas y Discos de Freno",
        "Brake Rotor Resurfacing": "Rectificado de Discos de Freno",
        "Complete Brake Service": "Servicio Completo de Frenos",
        "Thrust Angle Alignment": "Alineación de Ángulo de Empuje",
        # Detailing Services
        "Full Service Detailing": "Detallado Completo",
        "Interior Detailing": "Detallado Interior",
        "Exterior Detailing": "Detallado Exterior",
        "Touch Up Paint": "Retoque de Pintura",
        "Paintless Dent Repair": "Reparación de Abolladuras sin Pintura",
        # Car Wash Services
        "Express Car Wash": "Lavado Express",
        "Self Service Wash": "Lavado Autoservicio",
        "Hand Wash Service": "Lavado a Mano",
        "Premium Car Wash": "Lavado Premium",
        "Deluxe Wash Package": "Paquete de Lavado Deluxe",
        # Diagnostic Services
        "Engine Diagnostic": "Diagnóstico de Motor",
        "Check Engine Light Diagnosis": "Diagnóstico de Luz de Motor",
        "OBD Diagnostic Scan": "Escaneo Diagnóstico OBD",
        # Additional Alignment Services
        "Rear Wheel Alignment": "Alineación Trasera",
        # AC Services
        "AC System Service": "Servicio de Sistema de Aire Acondicionado",
        "AC System Inspection": "Inspección de Sistema de Aire Acondicionado",
        "AC Refrigerant Recharge": "Recarga de Refrigerante de A/C",
        "AC System Recharge": "Recarga de Sistema de A/C",
        # Body Repair Services
        "Clear Coat Repair": "Reparación de Capa Transparente",
        "Paint Scratch Repair": "Reparación de Rayones de Pintura",
        "Body Panel Repair": "Reparación de Panel de Carrocería",
        "Frame Straightening": "Enderezado de Chasis",
        "Collision Repair": "Reparación de Colisión",
        "Dent Removal": "Eliminación de Abolladuras",
        "Paintless Dent Removal": "Eliminación de Abolladuras sin Pintura",
        # Services that are already in Spanish (to skip)
        # These will be detected by _is_mostly_english() returning False
    }

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Solo muestra qué servicios se traducirían sin hacer cambios",
        )
        parser.add_argument(
            "--empresa",
            type=int,
            help="ID de empresa específica (opcional, por defecto todas)",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        empresa_id = options.get("empresa")

        self.stdout.write(
            self.style.SUCCESS(
                "🔍 Buscando servicios con nombres en inglés que necesitan traducción..."
            )
        )

        # Buscar servicios que tienen nombres en español pero están en inglés
        if empresa_id:
            servicios_qs = Servicio.objects.filter(empresa_id=empresa_id)
        else:
            servicios_qs = Servicio.objects.all()

        # Buscar servicios que necesitan traducción
        servicios_necesitan_traduccion = []

        for servicio in servicios_qs.distinct():
            # Obtener nombre en inglés
            try:
                nombre_en_obj = servicio.names.get(language="en", is_default=True)
                nombre_en = nombre_en_obj.label
            except ServicioName.DoesNotExist:
                # Si no tiene nombre en inglés, usar el nombre base
                nombre_en = servicio.nombre

            # Obtener nombre en español
            try:
                nombre_es_obj = servicio.names.get(language="es", is_default=True)
                nombre_es = nombre_es_obj.label

                # Si el nombre en español es igual al nombre en inglés, necesita traducción
                # O si el nombre en español contiene muchas palabras en inglés
                if nombre_es == nombre_en or self._is_mostly_english(nombre_es):
                    servicios_necesitan_traduccion.append((servicio, nombre_en, nombre_es_obj))
                # Si el nombre en español ya está en español (no es inglés), saltarlo
                elif not self._is_mostly_english(nombre_es) and nombre_es != nombre_en:
                    # Ya está en español, no necesita traducción
                    pass
            except ServicioName.DoesNotExist:
                # Si no tiene nombre en español, también necesita traducción
                servicios_necesitan_traduccion.append((servicio, nombre_en, None))

        total_servicios = len(servicios_necesitan_traduccion)
        self.stdout.write(
            self.style.NOTICE(
                f"📋 Encontrados {total_servicios} servicios que necesitan traducción al español"
            )
        )

        if total_servicios == 0:
            self.stdout.write(
                self.style.SUCCESS(
                    "✅ Todos los servicios ya tienen traducción correcta en español"
                )
            )
            return

        creados = 0
        actualizados = 0
        sin_traduccion = []

        for servicio, nombre_en, nombre_es_obj in servicios_necesitan_traduccion:
            # Buscar traducción en el diccionario
            traduccion_es = self.TRADUCCIONES.get(nombre_en, None)

            # Si no hay traducción directa, intentar búsqueda parcial (más flexible)
            if not traduccion_es:
                nombre_en_lower = nombre_en.lower()
                mejor_coincidencia = None
                mejor_longitud = 0

                for key, value in self.TRADUCCIONES.items():
                    key_lower = key.lower()
                    # Si la clave está contenida en el nombre o viceversa
                    if key_lower in nombre_en_lower or nombre_en_lower in key_lower:
                        # Preferir la coincidencia más larga
                        if len(key) > mejor_longitud:
                            mejor_coincidencia = value
                            mejor_longitud = len(key)

                if mejor_coincidencia:
                    traduccion_es = mejor_coincidencia

            # Si aún no hay traducción, usar el nombre base como fallback
            if not traduccion_es:
                sin_traduccion.append((servicio.id, nombre_en))
                continue

            if nombre_es_obj:
                # Actualizar la traducción existente
                if not dry_run:
                    nombre_es_obj.label = traduccion_es
                    nombre_es_obj.save()
                actualizados += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"   ✅ Actualizado: '{nombre_en}' → '{traduccion_es}' (ID: {servicio.id})"
                    )
                )
            else:
                # Crear nueva traducción
                if not dry_run:
                    # Primero, desmarcar cualquier otro nombre en español como default si existe
                    servicio.names.filter(language="es").update(is_default=False)

                    ServicioName.objects.create(
                        servicio=servicio,
                        language="es",
                        label=traduccion_es,
                        is_default=True,
                    )
                creados += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"   ✅ Creado: '{nombre_en}' → '{traduccion_es}' (ID: {servicio.id})"
                    )
                )

        # Resumen
        self.stdout.write("\n" + "=" * 60)
        if dry_run:
            self.stdout.write(self.style.WARNING("🔍 MODO DRY-RUN - No se hicieron cambios"))
        else:
            self.stdout.write(self.style.SUCCESS(f"✅ Traducciones creadas: {creados}"))
            self.stdout.write(self.style.SUCCESS(f"✅ Traducciones actualizadas: {actualizados}"))

        if sin_traduccion:
            self.stdout.write(
                self.style.ERROR(
                    f"\n⚠️  {len(sin_traduccion)} servicios necesitan traducción manual:"
                )
            )
            for servicio_id, nombre in sin_traduccion[:20]:  # Limitar a 20 para no saturar
                self.stdout.write(self.style.ERROR(f"   - ID {servicio_id}: {nombre}"))
            if len(sin_traduccion) > 20:
                self.stdout.write(self.style.ERROR(f"   ... y {len(sin_traduccion) - 20} más"))

        self.stdout.write(self.style.SUCCESS("\n🎉 Proceso completado"))

    def _is_mostly_english(self, text):
        """Verifica si un texto es mayormente inglés (contiene muchas palabras en inglés)"""
        # Palabras comunes en inglés que no deberían estar en español
        english_words = {
            "replacement",
            "repair",
            "service",
            "change",
            "installation",
            "testing",
            "cleaning",
            "flush",
            "adjustment",
            "rebuild",
            "oil",
            "filter",
            "air",
            "fuel",
            "brake",
            "engine",
            "transmission",
            "battery",
            "tire",
            "wheel",
            "belt",
            "fluid",
            "coolant",
            "head",
            "gasket",
            "timing",
            "valve",
            "mount",
            "cylinder",
            "conventional",
            "synthetic",
            "high",
            "mileage",
            "cabin",
            "serpentine",
            "accessory",
            "power",
            "steering",
            "front",
            "rear",
            "alignment",
            "balancing",
            "rotation",
            "puncture",
            "sidewall",
            "new",
            "seasonal",
            "run",
            "flat",
            "mounting",
            "with",
            "inspection",
            "road",
            "force",
            "chain",
            "alternator",
            "starter",
            "solenoid",
            "terminal",
            "pvc",
            "egr",
            "mass",
            "flow",
            "sensor",
            "oxygen",
            "windscreen",
            "windshield",
            "wiper",
            "headlight",
            "taillight",
            "turn",
            "signal",
            "and",
            "the",
            "of",
            "a",
            "an",
        }
        palabras = set(text.lower().split())
        palabras_ingles = palabras.intersection(english_words)
        # Si más del 30% de las palabras son inglesas, considerar que es inglés
        return len(palabras) > 0 and len(palabras_ingles) / len(palabras) > 0.3
