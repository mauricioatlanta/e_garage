"""
Catálogo de piezas comunes para generar inventario automático al crear vehículo de desarme.
Cada pieza tiene: codigo, nombre, zona (categoría), precio_base (sugerido).
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
    ("MOT-01", "Alternador", ZONA_MOTOR, Decimal("90000")),
    ("MOT-02", "Arranque", ZONA_MOTOR, Decimal("75000")),
    ("MOT-03", "Motor completo", ZONA_MOTOR, Decimal("450000")),
    ("MOT-04", "Bloque motor", ZONA_MOTOR, Decimal("180000")),
    ("MOT-05", "Tapa de cilindros", ZONA_MOTOR, Decimal("95000")),
    ("MOT-06", "Distribuidor", ZONA_MOTOR, Decimal("35000")),
    ("MOT-07", "Bomba de agua", ZONA_MOTOR, Decimal("45000")),
    ("MOT-08", "Radiador", ZONA_MOTOR, Decimal("65000")),
    ("MOT-09", "Ventilador radiador", ZONA_MOTOR, Decimal("25000")),
    ("MOT-10", "Múltiple admisión", ZONA_MOTOR, Decimal("55000")),
    ("MOT-11", "Múltiple escape", ZONA_MOTOR, Decimal("48000")),
    ("MOT-12", "Turbo", ZONA_MOTOR, Decimal("120000")),
    ("MOT-13", "Intercooler", ZONA_MOTOR, Decimal("75000")),
    ("MOT-14", "Bomba inyectora", ZONA_MOTOR, Decimal("85000")),
    ("MOT-15", "Inyectores (set)", ZONA_MOTOR, Decimal("95000")),
    # Carrocería
    ("CAR-01", "Capot", ZONA_CARROCERIA, Decimal("85000")),
    ("CAR-02", "Puerta delantera izq", ZONA_CARROCERIA, Decimal("75000")),
    ("CAR-03", "Puerta delantera der", ZONA_CARROCERIA, Decimal("75000")),
    ("CAR-04", "Puerta trasera izq", ZONA_CARROCERIA, Decimal("65000")),
    ("CAR-05", "Puerta trasera der", ZONA_CARROCERIA, Decimal("65000")),
    ("CAR-06", "Baguetera", ZONA_CARROCERIA, Decimal("95000")),
    ("CAR-07", "Tapa baúl", ZONA_CARROCERIA, Decimal("55000")),
    ("CAR-08", "Parachoques delantero", ZONA_CARROCERIA, Decimal("45000")),
    ("CAR-09", "Parachoques trasero", ZONA_CARROCERIA, Decimal("40000")),
    ("CAR-10", "Guardabarros izq", ZONA_CARROCERIA, Decimal("35000")),
    ("CAR-11", "Guardabarros der", ZONA_CARROCERIA, Decimal("35000")),
    ("CAR-12", "Puerta maletero", ZONA_CARROCERIA, Decimal("38000")),
    ("CAR-13", "Tapa de bencinera", ZONA_CARROCERIA, Decimal("18000")),
    ("CAR-14", "Paragolpes delantero", ZONA_CARROCERIA, Decimal("52000")),
    ("CAR-15", "Paragolpes trasero", ZONA_CARROCERIA, Decimal("48000")),
    # Interior
    ("INT-01", "Asiento delantero izq", ZONA_INTERIOR, Decimal("75000")),
    ("INT-02", "Asiento delantero der", ZONA_INTERIOR, Decimal("75000")),
    ("INT-03", "Asiento trasero", ZONA_INTERIOR, Decimal("55000")),
    ("INT-04", "Tablero completo", ZONA_INTERIOR, Decimal("95000")),
    ("INT-05", "Volante", ZONA_INTERIOR, Decimal("35000")),
    ("INT-06", "Palanca de cambios", ZONA_INTERIOR, Decimal("25000")),
    ("INT-07", "Consola central", ZONA_INTERIOR, Decimal("28000")),
    ("INT-08", "Alfombra delantera", ZONA_INTERIOR, Decimal("15000")),
    ("INT-09", "Alfombra trasera", ZONA_INTERIOR, Decimal("12000")),
    ("INT-10", "Airbag conductor", ZONA_INTERIOR, Decimal("85000")),
    ("INT-11", "Airbag pasajero", ZONA_INTERIOR, Decimal("85000")),
    ("INT-12", "Retrovisor interior", ZONA_INTERIOR, Decimal("12000")),
    ("INT-13", "Tapacubos volante", ZONA_INTERIOR, Decimal("8000")),
    ("INT-14", "Cinturones de seguridad (set)", ZONA_INTERIOR, Decimal("35000")),
    ("INT-15", "Espejo retrovisor izq", ZONA_INTERIOR, Decimal("22000")),
    ("INT-16", "Espejo retrovisor der", ZONA_INTERIOR, Decimal("22000")),
    # Suspensión
    ("SUS-01", "Amortiguador delantero izq", ZONA_SUSPENSION, Decimal("45000")),
    ("SUS-02", "Amortiguador delantero der", ZONA_SUSPENSION, Decimal("45000")),
    ("SUS-03", "Amortiguador trasero izq", ZONA_SUSPENSION, Decimal("38000")),
    ("SUS-04", "Amortiguador trasero der", ZONA_SUSPENSION, Decimal("38000")),
    ("SUS-05", "Resorte delantero (par)", ZONA_SUSPENSION, Decimal("25000")),
    ("SUS-06", "Resorte trasero (par)", ZONA_SUSPENSION, Decimal("22000")),
    ("SUS-07", "Brazo inferior izq", ZONA_SUSPENSION, Decimal("55000")),
    ("SUS-08", "Brazo inferior der", ZONA_SUSPENSION, Decimal("55000")),
    ("SUS-09", "Rótula dirección izq", ZONA_SUSPENSION, Decimal("25000")),
    ("SUS-10", "Rótula dirección der", ZONA_SUSPENSION, Decimal("25000")),
    ("SUS-11", "Maza delantera izq", ZONA_SUSPENSION, Decimal("45000")),
    ("SUS-12", "Maza delantera der", ZONA_SUSPENSION, Decimal("45000")),
    ("SUS-13", "Dirección hidráulica", ZONA_SUSPENSION, Decimal("85000")),
    ("SUS-14", "Barra estabilizadora", ZONA_SUSPENSION, Decimal("35000")),
    ("SUS-15", "Cremallera", ZONA_SUSPENSION, Decimal("55000")),
    # Iluminación
    ("ILU-01", "Faro izquierdo", ZONA_ILUMINACION, Decimal("85000")),
    ("ILU-02", "Faro derecho", ZONA_ILUMINACION, Decimal("85000")),
    ("ILU-03", "Luz trasera izq", ZONA_ILUMINACION, Decimal("45000")),
    ("ILU-04", "Luz trasera der", ZONA_ILUMINACION, Decimal("45000")),
    ("ILU-05", "Luz de neblina izq", ZONA_ILUMINACION, Decimal("28000")),
    ("ILU-06", "Luz de neblina der", ZONA_ILUMINACION, Decimal("28000")),
    ("ILU-07", "Luz de techo", ZONA_ILUMINACION, Decimal("12000")),
    ("ILU-08", "Intermitente izq", ZONA_ILUMINACION, Decimal("15000")),
    ("ILU-09", "Intermitente der", ZONA_ILUMINACION, Decimal("15000")),
    ("ILU-10", "Luz de placa", ZONA_ILUMINACION, Decimal("8000")),
    ("ILU-11", "Faro trasero izq", ZONA_ILUMINACION, Decimal("38000")),
    ("ILU-12", "Faro trasero der", ZONA_ILUMINACION, Decimal("38000")),
    # Electrónica
    ("ELE-01", "Radio", ZONA_ELECTRONICA, Decimal("55000")),
    ("ELE-02", "ECU / computadora", ZONA_ELECTRONICA, Decimal("95000")),
    ("ELE-03", "Batería", ZONA_ELECTRONICA, Decimal("45000")),
    ("ELE-04", "Sensores ABS", ZONA_ELECTRONICA, Decimal("35000")),
    ("ELE-05", "Ventana delantera izq", ZONA_ELECTRONICA, Decimal("28000")),
    ("ELE-06", "Ventana delantera der", ZONA_ELECTRONICA, Decimal("28000")),
    ("ELE-07", "Ventana trasera izq", ZONA_ELECTRONICA, Decimal("22000")),
    ("ELE-08", "Ventana trasera der", ZONA_ELECTRONICA, Decimal("22000")),
    ("ELE-09", "Motor elevavidrios izq", ZONA_ELECTRONICA, Decimal("25000")),
    ("ELE-10", "Motor elevavidrios der", ZONA_ELECTRONICA, Decimal("25000")),
    ("ELE-11", "Sensores SRS", ZONA_ELECTRONICA, Decimal("45000")),
    ("ELE-12", "Fusibles y relay (set)", ZONA_ELECTRONICA, Decimal("12000")),
    ("ELE-13", "Cableado principal", ZONA_ELECTRONICA, Decimal("65000")),
    ("ELE-14", "Bomba combustible", ZONA_ELECTRONICA, Decimal("55000")),
    ("ELE-15", "Estarter", ZONA_ELECTRONICA, Decimal("45000")),
    # Escape
    ("ESC-01", "Convertidor catalítico", ZONA_ESCAPE, Decimal("85000")),
    ("ESC-02", "Sonda lambda", ZONA_ESCAPE, Decimal("35000")),
    ("ESC-03", "Mofle central", ZONA_ESCAPE, Decimal("45000")),
    ("ESC-04", "Mofle trasero", ZONA_ESCAPE, Decimal("38000")),
    ("ESC-05", "Caño escape completo", ZONA_ESCAPE, Decimal("95000")),
    ("ESC-06", "Flexible escape", ZONA_ESCAPE, Decimal("25000")),
    ("ESC-07", "Soporte escape", ZONA_ESCAPE, Decimal("12000")),
    ("ESC-08", "Tapón escape", ZONA_ESCAPE, Decimal("8000")),
    # Ruedas
    ("RUE-01", 'Rueda 15" (con neumático)', ZONA_RUEDAS, Decimal("55000")),
    ("RUE-02", 'Rueda 16" (con neumático)', ZONA_RUEDAS, Decimal("65000")),
    ("RUE-03", 'Rueda 17" (con neumático)', ZONA_RUEDAS, Decimal("75000")),
    ("RUE-04", "Disco freno delantero (par)", ZONA_RUEDAS, Decimal("65000")),
    ("RUE-05", "Disco freno trasero (par)", ZONA_RUEDAS, Decimal("55000")),
    ("RUE-06", "Tambor freno trasero (par)", ZONA_RUEDAS, Decimal("45000")),
    ("RUE-07", "Pinza freno delantera izq", ZONA_RUEDAS, Decimal("75000")),
    ("RUE-08", "Pinza freno delantera der", ZONA_RUEDAS, Decimal("75000")),
    ("RUE-09", "Pastillas freno (set)", ZONA_RUEDAS, Decimal("35000")),
    ("RUE-10", "Tambor (unidad)", ZONA_RUEDAS, Decimal("25000")),
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
