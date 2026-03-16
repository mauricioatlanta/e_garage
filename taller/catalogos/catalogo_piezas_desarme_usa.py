"""
Catálogo de piezas de desarme para mercado USA.
Estructura preparada para búsqueda, scanner e inventario automático.
Incluye: código, categoría, nombres oficial/slang y sinónimos (ES/EN).
"""

CATALOGO_PIEZAS_DESARME_USA = [
    # --- ENGINE (motor) ---
    {
        "codigo": "engine_assembly",
        "categoria": "engine",
        "nombre_es": "Motor completo",
        "nombre_en_oficial": "Engine Assembly",
        "nombre_en_slang": "Engine",
        "sinonimos_en": ["engine", "motor"],
        "sinonimos_es": ["motor completo"],
    },
    {
        "codigo": "engine_block",
        "categoria": "engine",
        "nombre_es": "Bloque de motor",
        "nombre_en_oficial": "Engine Block",
        "nombre_en_slang": "Block",
        "sinonimos_en": [],
        "sinonimos_es": [],
    },
    {
        "codigo": "cylinder_head",
        "categoria": "engine",
        "nombre_es": "Culata",
        "nombre_en_oficial": "Cylinder Head",
        "nombre_en_slang": "Head",
        "sinonimos_en": [],
        "sinonimos_es": [],
    },
    {
        "codigo": "camshaft",
        "categoria": "engine",
        "nombre_es": "Árbol de levas",
        "nombre_en_oficial": "Camshaft",
        "nombre_en_slang": "Cam",
        "sinonimos_en": [],
        "sinonimos_es": [],
    },
    {
        "codigo": "crankshaft",
        "categoria": "engine",
        "nombre_es": "Cigüeñal",
        "nombre_en_oficial": "Crankshaft",
        "nombre_en_slang": "Crank",
        "sinonimos_en": [],
        "sinonimos_es": [],
    },
    {
        "codigo": "piston",
        "categoria": "engine",
        "nombre_es": "Pistón",
        "nombre_en_oficial": "Piston",
        "nombre_en_slang": "Piston",
        "sinonimos_en": [],
        "sinonimos_es": [],
    },
    {
        "codigo": "valve_cover",
        "categoria": "engine",
        "nombre_es": "Tapa de válvulas",
        "nombre_en_oficial": "Valve Cover",
        "nombre_en_slang": "Valve cover",
        "sinonimos_en": [],
        "sinonimos_es": [],
    },
    {
        "codigo": "oil_pan",
        "categoria": "engine",
        "nombre_es": "Cárter de aceite",
        "nombre_en_oficial": "Oil Pan",
        "nombre_en_slang": "Oil pan",
        "sinonimos_en": [],
        "sinonimos_es": [],
    },
    # --- DRIVETRAIN ---
    {
        "codigo": "transmission_auto",
        "categoria": "drivetrain",
        "nombre_es": "Transmisión automática",
        "nombre_en_oficial": "Automatic Transmission",
        "nombre_en_slang": "Transmission",
        "sinonimos_en": [],
        "sinonimos_es": [],
    },
    {
        "codigo": "transmission_manual",
        "categoria": "drivetrain",
        "nombre_es": "Transmisión manual",
        "nombre_en_oficial": "Manual Transmission",
        "nombre_en_slang": "Transmission",
        "sinonimos_en": [],
        "sinonimos_es": [],
    },
    {
        "codigo": "torque_converter",
        "categoria": "drivetrain",
        "nombre_es": "Convertidor de torque",
        "nombre_en_oficial": "Torque Converter",
        "nombre_en_slang": "Converter",
        "sinonimos_en": [],
        "sinonimos_es": [],
    },
    {
        "codigo": "driveshaft",
        "categoria": "drivetrain",
        "nombre_es": "Cardán",
        "nombre_en_oficial": "Driveshaft",
        "nombre_en_slang": "Drive shaft",
        "sinonimos_en": [],
        "sinonimos_es": [],
    },
    {
        "codigo": "rear_differential",
        "categoria": "drivetrain",
        "nombre_es": "Diferencial trasero",
        "nombre_en_oficial": "Rear Differential",
        "nombre_en_slang": "Diff",
        "sinonimos_en": [],
        "sinonimos_es": [],
    },
    # --- SUSPENSION ---
    {
        "codigo": "front_shock",
        "categoria": "suspension",
        "nombre_es": "Amortiguador delantero",
        "nombre_en_oficial": "Front Shock Absorber",
        "nombre_en_slang": "Front shock",
        "sinonimos_en": [],
        "sinonimos_es": [],
    },
    {
        "codigo": "rear_shock",
        "categoria": "suspension",
        "nombre_es": "Amortiguador trasero",
        "nombre_en_oficial": "Rear Shock Absorber",
        "nombre_en_slang": "Rear shock",
        "sinonimos_en": [],
        "sinonimos_es": [],
    },
    {
        "codigo": "strut_assembly",
        "categoria": "suspension",
        "nombre_es": "Strut completo",
        "nombre_en_oficial": "Strut Assembly",
        "nombre_en_slang": "Strut",
        "sinonimos_en": [],
        "sinonimos_es": [],
    },
    {
        "codigo": "control_arm",
        "categoria": "suspension",
        "nombre_es": "Bandeja de suspensión",
        "nombre_en_oficial": "Control Arm",
        "nombre_en_slang": "Control arm",
        "sinonimos_en": [],
        "sinonimos_es": [],
    },
    {
        "codigo": "sway_bar",
        "categoria": "suspension",
        "nombre_es": "Barra estabilizadora",
        "nombre_en_oficial": "Stabilizer Bar",
        "nombre_en_slang": "Sway bar",
        "sinonimos_en": [],
        "sinonimos_es": [],
    },
    {
        "codigo": "sway_bar_link",
        "categoria": "suspension",
        "nombre_es": "Bieleta",
        "nombre_en_oficial": "Sway Bar Link",
        "nombre_en_slang": "Sway link",
        "sinonimos_en": [],
        "sinonimos_es": [],
    },
    # --- BRAKES ---
    {
        "codigo": "brake_rotor",
        "categoria": "brakes",
        "nombre_es": "Disco de freno",
        "nombre_en_oficial": "Brake Rotor",
        "nombre_en_slang": "Rotor",
        "sinonimos_en": [],
        "sinonimos_es": [],
    },
    {
        "codigo": "brake_caliper",
        "categoria": "brakes",
        "nombre_es": "Caliper de freno",
        "nombre_en_oficial": "Brake Caliper",
        "nombre_en_slang": "Caliper",
        "sinonimos_en": [],
        "sinonimos_es": [],
    },
    {
        "codigo": "brake_master_cylinder",
        "categoria": "brakes",
        "nombre_es": "Bomba de freno",
        "nombre_en_oficial": "Brake Master Cylinder",
        "nombre_en_slang": "Master cylinder",
        "sinonimos_en": [],
        "sinonimos_es": [],
    },
    {
        "codigo": "brake_booster",
        "categoria": "brakes",
        "nombre_es": "Servo freno",
        "nombre_en_oficial": "Brake Booster",
        "nombre_en_slang": "Booster",
        "sinonimos_en": [],
        "sinonimos_es": [],
    },
    # --- COOLING ---
    {
        "codigo": "radiator",
        "categoria": "cooling",
        "nombre_es": "Radiador",
        "nombre_en_oficial": "Radiator",
        "nombre_en_slang": "Radiator",
        "sinonimos_en": [],
        "sinonimos_es": [],
    },
    {
        "codigo": "radiator_fan",
        "categoria": "cooling",
        "nombre_es": "Electroventilador",
        "nombre_en_oficial": "Radiator Fan",
        "nombre_en_slang": "Fan",
        "sinonimos_en": [],
        "sinonimos_es": [],
    },
    {
        "codigo": "water_pump",
        "categoria": "cooling",
        "nombre_es": "Bomba de agua",
        "nombre_en_oficial": "Water Pump",
        "nombre_en_slang": "Water pump",
        "sinonimos_en": [],
        "sinonimos_es": [],
    },
    # --- ELECTRICAL ---
    {
        "codigo": "alternator",
        "categoria": "electrical",
        "nombre_es": "Alternador",
        "nombre_en_oficial": "Alternator",
        "nombre_en_slang": "Alternator",
        "sinonimos_en": [],
        "sinonimos_es": [],
    },
    {
        "codigo": "starter_motor",
        "categoria": "electrical",
        "nombre_es": "Motor de arranque",
        "nombre_en_oficial": "Starter Motor",
        "nombre_en_slang": "Starter",
        "sinonimos_en": [],
        "sinonimos_es": [],
    },
    {
        "codigo": "ecu",
        "categoria": "electrical",
        "nombre_es": "Computadora motor",
        "nombre_en_oficial": "Engine Control Module",
        "nombre_en_slang": "ECU",
        "sinonimos_en": [],
        "sinonimos_es": [],
    },
    {
        "codigo": "battery",
        "categoria": "electrical",
        "nombre_es": "Batería",
        "nombre_en_oficial": "Battery",
        "nombre_en_slang": "Battery",
        "sinonimos_en": [],
        "sinonimos_es": [],
    },
    # --- BODY ---
    {
        "codigo": "front_bumper_cover",
        "categoria": "body",
        "nombre_es": "Parachoques delantero",
        "nombre_en_oficial": "Front Bumper Cover",
        "nombre_en_slang": "Front bumper",
        "sinonimos_en": [],
        "sinonimos_es": [],
    },
    {
        "codigo": "rear_bumper_cover",
        "categoria": "body",
        "nombre_es": "Parachoques trasero",
        "nombre_en_oficial": "Rear Bumper Cover",
        "nombre_en_slang": "Rear bumper",
        "sinonimos_en": [],
        "sinonimos_es": [],
    },
    {
        "codigo": "hood",
        "categoria": "body",
        "nombre_es": "Capó",
        "nombre_en_oficial": "Hood",
        "nombre_en_slang": "Hood",
        "sinonimos_en": [],
        "sinonimos_es": [],
    },
    {
        "codigo": "fender",
        "categoria": "body",
        "nombre_es": "Tapabarro",
        "nombre_en_oficial": "Fender",
        "nombre_en_slang": "Fender",
        "sinonimos_en": [],
        "sinonimos_es": [],
    },
    {
        "codigo": "door",
        "categoria": "body",
        "nombre_es": "Puerta",
        "nombre_en_oficial": "Door Assembly",
        "nombre_en_slang": "Door",
        "sinonimos_en": [],
        "sinonimos_es": [],
    },
]


def get_categorias_usa():
    """Devuelve las categorías únicas del catálogo USA (ordenadas)."""
    cats = sorted({p["categoria"] for p in CATALOGO_PIEZAS_DESARME_USA})
    return cats


def get_pieza_by_codigo(codigo):
    """Devuelve la entrada del catálogo por código o None."""
    for p in CATALOGO_PIEZAS_DESARME_USA:
        if p["codigo"] == codigo:
            return p
    return None


def buscar_piezas_usa(query, lang="en"):
    """
    Búsqueda por texto sobre el catálogo USA.
    query: término a buscar (minúsculas recomendado).
    lang: 'en' o 'es' para priorizar nombre/sinónimos en ese idioma.
    """
    q = (query or "").strip().lower()
    if not q:
        return []
    results = []
    for p in CATALOGO_PIEZAS_DESARME_USA:
        score = 0
        if q in (p.get("codigo") or "").lower():
            score += 10
        if q in (p.get("nombre_en_oficial") or "").lower():
            score += 5
        if q in (p.get("nombre_en_slang") or "").lower():
            score += 4
        if q in (p.get("nombre_es") or "").lower():
            score += 5
        if q in (p.get("categoria") or "").lower():
            score += 2
        for s in p.get("sinonimos_en") or []:
            if q in s.lower():
                score += 3
                break
        for s in p.get("sinonimos_es") or []:
            if q in s.lower():
                score += 3
                break
        if score > 0:
            results.append((score, p))
    results.sort(key=lambda x: -x[0])
    return [p for _, p in results]
