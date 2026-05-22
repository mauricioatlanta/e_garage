"""
Catálogo de piezas comunes para generar inventario automático al crear vehículo de desarme.
Cada pieza tiene: codigo, nombre, zona (categoría), precio_base (sugerido CLP 2026).
"""

from decimal import Decimal

# Zonas/categorías para el Scanner
ZONA_MOTOR = "Motor"
ZONA_CARROCERIA = "Carrocería"
ZONA_INTERIOR = "Interior"
ZONA_SUSPENSION = "Suspensión"
ZONA_ILUMINACION = "Iluminación"
ZONA_ELECTRONICA = "Electrónica"
ZONA_ESCAPE = "Escape"
ZONA_RUEDAS = "Ruedas"

CATALOGO_PIEZAS = [
    # Motor
    ("MOT-01", "Alternador", ZONA_MOTOR, Decimal("95000")),
    ("MOT-02", "Arranque", ZONA_MOTOR, Decimal("80000")),
    ("MOT-03", "Motor completo", ZONA_MOTOR, Decimal("850000")),
    ("MOT-04", "Bloque motor", ZONA_MOTOR, Decimal("250000")),
    ("MOT-05", "Tapa de cilindros", ZONA_MOTOR, Decimal("110000")),
    ("MOT-06", "Distribuidor", ZONA_MOTOR, Decimal("38000")),
    ("MOT-07", "Bomba de agua", ZONA_MOTOR, Decimal("48000")),
    ("MOT-08", "Radiador", ZONA_MOTOR, Decimal("72000")),
    ("MOT-09", "Ventilador radiador", ZONA_MOTOR, Decimal("28000")),
    ("MOT-10", "Múltiple admisión", ZONA_MOTOR, Decimal("60000")),
    ("MOT-11", "Múltiple escape", ZONA_MOTOR, Decimal("52000")),
    # MOT-12 Turbo y MOT-13 Intercooler → PIEZAS_OPCIONALES (no todos los autos los llevan)
    ("MOT-14", "Bomba inyectora", ZONA_MOTOR, Decimal("90000")),
    ("MOT-15", "Inyectores (set)", ZONA_MOTOR, Decimal("100000")),
    # Carrocería
    ("CAR-01", "Capot", ZONA_CARROCERIA, Decimal("90000")),
    ("CAR-02", "Puerta delantera izq", ZONA_CARROCERIA, Decimal("82000")),
    ("CAR-03", "Puerta delantera der", ZONA_CARROCERIA, Decimal("82000")),
    ("CAR-04", "Puerta trasera izq", ZONA_CARROCERIA, Decimal("72000")),
    ("CAR-05", "Puerta trasera der", ZONA_CARROCERIA, Decimal("72000")),
    ("CAR-06", "Baguetera", ZONA_CARROCERIA, Decimal("100000")),
    ("CAR-07", "Tapa baúl", ZONA_CARROCERIA, Decimal("62000")),
    ("CAR-08", "Parachoques delantero", ZONA_CARROCERIA, Decimal("52000")),
    ("CAR-09", "Parachoques trasero", ZONA_CARROCERIA, Decimal("48000")),
    ("CAR-10", "Guardabarros izq", ZONA_CARROCERIA, Decimal("42000")),
    ("CAR-11", "Guardabarros der", ZONA_CARROCERIA, Decimal("42000")),
    ("CAR-12", "Puerta maletero", ZONA_CARROCERIA, Decimal("48000")),
    ("CAR-13", "Tapa de bencinera", ZONA_CARROCERIA, Decimal("20000")),
    ("CAR-14", "Espejo lateral izq", ZONA_CARROCERIA, Decimal("48000")),
    ("CAR-15", "Espejo lateral der", ZONA_CARROCERIA, Decimal("48000")),
    ("CAR-16", "Vidrio parabrisas", ZONA_CARROCERIA, Decimal("120000")),
    ("CAR-17", "Vidrio luneta trasera", ZONA_CARROCERIA, Decimal("90000")),
    # Interior
    ("INT-01", "Asiento delantero izq", ZONA_INTERIOR, Decimal("80000")),
    ("INT-02", "Asiento delantero der", ZONA_INTERIOR, Decimal("80000")),
    ("INT-03", "Asiento trasero", ZONA_INTERIOR, Decimal("60000")),
    ("INT-04", "Tablero completo", ZONA_INTERIOR, Decimal("135000")),
    ("INT-05", "Volante", ZONA_INTERIOR, Decimal("38000")),
    ("INT-06", "Palanca de cambios", ZONA_INTERIOR, Decimal("28000")),
    ("INT-07", "Consola central", ZONA_INTERIOR, Decimal("32000")),
    ("INT-08", "Alfombra delantera", ZONA_INTERIOR, Decimal("18000")),
    ("INT-09", "Alfombra trasera", ZONA_INTERIOR, Decimal("15000")),
    ("INT-10", "Airbag conductor", ZONA_INTERIOR, Decimal("90000")),
    ("INT-11", "Airbag pasajero", ZONA_INTERIOR, Decimal("90000")),
    ("INT-12", "Retrovisor interior", ZONA_INTERIOR, Decimal("15000")),
    ("INT-13", "Tapacubos volante", ZONA_INTERIOR, Decimal("10000")),
    ("INT-14", "Cinturones de seguridad (set)", ZONA_INTERIOR, Decimal("42000")),
    # Suspensión
    ("SUS-01", "Amortiguador delantero izq", ZONA_SUSPENSION, Decimal("48000")),
    ("SUS-02", "Amortiguador delantero der", ZONA_SUSPENSION, Decimal("48000")),
    ("SUS-03", "Amortiguador trasero izq", ZONA_SUSPENSION, Decimal("40000")),
    ("SUS-04", "Amortiguador trasero der", ZONA_SUSPENSION, Decimal("40000")),
    ("SUS-05", "Resorte delantero (par)", ZONA_SUSPENSION, Decimal("28000")),
    ("SUS-06", "Resorte trasero (par)", ZONA_SUSPENSION, Decimal("25000")),
    ("SUS-07", "Brazo inferior izq", ZONA_SUSPENSION, Decimal("60000")),
    ("SUS-08", "Brazo inferior der", ZONA_SUSPENSION, Decimal("60000")),
    ("SUS-09", "Rótula dirección izq", ZONA_SUSPENSION, Decimal("28000")),
    ("SUS-10", "Rótula dirección der", ZONA_SUSPENSION, Decimal("28000")),
    ("SUS-11", "Maza delantera izq", ZONA_SUSPENSION, Decimal("48000")),
    ("SUS-12", "Maza delantera der", ZONA_SUSPENSION, Decimal("48000")),
    ("SUS-13", "Dirección hidráulica", ZONA_SUSPENSION, Decimal("90000")),
    ("SUS-14", "Barra estabilizadora", ZONA_SUSPENSION, Decimal("38000")),
    ("SUS-15", "Cremallera", ZONA_SUSPENSION, Decimal("65000")),
    # Iluminación
    ("ILU-01", "Óptico delantero izq", ZONA_ILUMINACION, Decimal("120000")),
    ("ILU-02", "Óptico delantero der", ZONA_ILUMINACION, Decimal("120000")),
    ("ILU-03", "Óptico trasero izq", ZONA_ILUMINACION, Decimal("55000")),
    ("ILU-04", "Óptico trasero der", ZONA_ILUMINACION, Decimal("55000")),
    ("ILU-05", "Luz de neblina izq", ZONA_ILUMINACION, Decimal("30000")),
    ("ILU-06", "Luz de neblina der", ZONA_ILUMINACION, Decimal("30000")),
    ("ILU-07", "Luz de techo", ZONA_ILUMINACION, Decimal("12000")),
    ("ILU-08", "Intermitente delantero izq", ZONA_ILUMINACION, Decimal("18000")),
    ("ILU-09", "Intermitente delantero der", ZONA_ILUMINACION, Decimal("18000")),
    ("ILU-10", "Luz de placa", ZONA_ILUMINACION, Decimal("8000")),
    ("ILU-11", "Tercer stop", ZONA_ILUMINACION, Decimal("18000")),
    ("ILU-12", "Luz diurna (DRL) izq", ZONA_ILUMINACION, Decimal("28000")),
    # Electrónica
    ("ELE-01", "Radio / pantalla multimedia", ZONA_ELECTRONICA, Decimal("68000")),
    ("ELE-02", "ECU / computadora motor", ZONA_ELECTRONICA, Decimal("115000")),
    ("ELE-03", "Batería", ZONA_ELECTRONICA, Decimal("50000")),
    ("ELE-04", "Sensores ABS (set)", ZONA_ELECTRONICA, Decimal("38000")),
    ("ELE-05", "Vidrio puerta del. izq", ZONA_ELECTRONICA, Decimal("30000")),
    ("ELE-06", "Vidrio puerta del. der", ZONA_ELECTRONICA, Decimal("30000")),
    ("ELE-07", "Vidrio puerta tras. izq", ZONA_ELECTRONICA, Decimal("24000")),
    ("ELE-08", "Vidrio puerta tras. der", ZONA_ELECTRONICA, Decimal("24000")),
    ("ELE-09", "Motor elevavidrios izq", ZONA_ELECTRONICA, Decimal("28000")),
    ("ELE-10", "Motor elevavidrios der", ZONA_ELECTRONICA, Decimal("28000")),
    ("ELE-11", "Sensores SRS", ZONA_ELECTRONICA, Decimal("48000")),
    ("ELE-12", "Fusibles y relay (set)", ZONA_ELECTRONICA, Decimal("15000")),
    ("ELE-13", "Cableado principal", ZONA_ELECTRONICA, Decimal("70000")),
    ("ELE-14", "Bomba combustible", ZONA_ELECTRONICA, Decimal("60000")),
    ("ELE-15", "Estarter", ZONA_ELECTRONICA, Decimal("48000")),
    ("ELE-16", "Módulo airbag (SRS)", ZONA_ELECTRONICA, Decimal("78000")),
    ("ELE-17", "Sensor parqueo trasero (set)", ZONA_ELECTRONICA, Decimal("22000")),
    ("ELE-18", "Cámara de retroceso", ZONA_ELECTRONICA, Decimal("35000")),
    # Escape
    ("ESC-01", "Catalizador", ZONA_ESCAPE, Decimal("180000")),
    ("ESC-02", "Sonda lambda", ZONA_ESCAPE, Decimal("38000")),
    ("ESC-03", "Mofle central", ZONA_ESCAPE, Decimal("48000")),
    ("ESC-04", "Mofle trasero", ZONA_ESCAPE, Decimal("42000")),
    ("ESC-05", "Caño escape completo", ZONA_ESCAPE, Decimal("100000")),
    ("ESC-06", "Flexible escape", ZONA_ESCAPE, Decimal("28000")),
    ("ESC-07", "Soporte escape", ZONA_ESCAPE, Decimal("14000")),
    ("ESC-08", "Tapón escape", ZONA_ESCAPE, Decimal("8000")),
    # Ruedas
    ("RUE-01", 'Rueda 15" (con neumático)', ZONA_RUEDAS, Decimal("65000")),
    ("RUE-02", 'Rueda 16" (con neumático)', ZONA_RUEDAS, Decimal("78000")),
    ("RUE-03", 'Rueda 17" (con neumático)', ZONA_RUEDAS, Decimal("90000")),
    ("RUE-04", "Disco freno delantero (par)", ZONA_RUEDAS, Decimal("70000")),
    ("RUE-05", "Disco freno trasero (par)", ZONA_RUEDAS, Decimal("60000")),
    ("RUE-06", "Tambor freno trasero (par)", ZONA_RUEDAS, Decimal("50000")),
    ("RUE-07", "Pinza freno delantera izq", ZONA_RUEDAS, Decimal("82000")),
    ("RUE-08", "Pinza freno delantera der", ZONA_RUEDAS, Decimal("82000")),
    ("RUE-09", "Pastillas freno (set)", ZONA_RUEDAS, Decimal("38000")),
    ("RUE-10", "Tambor (unidad)", ZONA_RUEDAS, Decimal("28000")),
]

# Piezas opcionales: no presentes en todos los vehículos.
# Agregar manualmente al inventario según el vehículo específico.
PIEZAS_OPCIONALES = [
    ("OPC-01", "Turbo", ZONA_MOTOR, Decimal("200000")),
    ("OPC-02", "Intercooler", ZONA_MOTOR, Decimal("90000")),
]

# Zonas para UI del blueprint
ZONAS_ORDEN = [
    ZONA_MOTOR,
    ZONA_CARROCERIA,
    ZONA_INTERIOR,
    ZONA_SUSPENSION,
    ZONA_ILUMINACION,
    ZONA_ELECTRONICA,
    ZONA_ESCAPE,
    ZONA_RUEDAS,
]
