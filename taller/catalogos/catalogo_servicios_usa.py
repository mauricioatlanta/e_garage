"""
Catálogo de servicios automotrices para mercado USA.
Para uso por suscriptores eGarage: nombres en español, inglés técnico y slang de taller.
Estructura preparada para búsqueda y uso en documentos/cotizaciones.
"""

SERVICIOS_AUTOMOTRICES_USA = [
    # --- MAINTENANCE (mantenimiento) ---
    {
        "codigo": "oil_change",
        "categoria": "maintenance",
        "nombre_es": "Cambio de aceite",
        "nombre_en_oficial": "Oil Change",
        "nombre_en_slang": "Oil change",
        "sinonimos_en": ["oil service"],
        "sinonimos_es": ["cambio de aceite"],
    },
    {
        "codigo": "oil_filter_replacement",
        "categoria": "maintenance",
        "nombre_es": "Cambio de filtro de aceite",
        "nombre_en_oficial": "Oil Filter Replacement",
        "nombre_en_slang": "Oil filter",
        "sinonimos_en": [],
        "sinonimos_es": [],
    },
    {
        "codigo": "air_filter_replacement",
        "categoria": "maintenance",
        "nombre_es": "Cambio filtro de aire",
        "nombre_en_oficial": "Air Filter Replacement",
        "nombre_en_slang": "Air filter",
        "sinonimos_en": [],
        "sinonimos_es": [],
    },
    {
        "codigo": "cabin_filter_replacement",
        "categoria": "maintenance",
        "nombre_es": "Cambio filtro cabina",
        "nombre_en_oficial": "Cabin Air Filter Replacement",
        "nombre_en_slang": "Cabin filter",
        "sinonimos_en": [],
        "sinonimos_es": [],
    },
    {
        "codigo": "spark_plug_replacement",
        "categoria": "maintenance",
        "nombre_es": "Cambio de bujías",
        "nombre_en_oficial": "Spark Plug Replacement",
        "nombre_en_slang": "Spark plugs",
        "sinonimos_en": [],
        "sinonimos_es": [],
    },
    # --- BRAKES ---
    {
        "codigo": "brake_replacement",
        "categoria": "brakes",
        "nombre_es": "Cambio de frenos",
        "nombre_en_oficial": "Brake Replacement",
        "nombre_en_slang": "Brake job",
        "sinonimos_en": [],
        "sinonimos_es": [],
    },
    {
        "codigo": "brake_pad_replacement",
        "categoria": "brakes",
        "nombre_es": "Cambio pastillas freno",
        "nombre_en_oficial": "Brake Pad Replacement",
        "nombre_en_slang": "Pads",
        "sinonimos_en": [],
        "sinonimos_es": [],
    },
    {
        "codigo": "brake_rotor_replacement",
        "categoria": "brakes",
        "nombre_es": "Cambio discos freno",
        "nombre_en_oficial": "Brake Rotor Replacement",
        "nombre_en_slang": "Rotor replacement",
        "sinonimos_en": [],
        "sinonimos_es": [],
    },
    {
        "codigo": "brake_fluid_flush",
        "categoria": "brakes",
        "nombre_es": "Cambio líquido de frenos",
        "nombre_en_oficial": "Brake Fluid Flush",
        "nombre_en_slang": "Brake fluid",
        "sinonimos_en": [],
        "sinonimos_es": [],
    },
    # --- SUSPENSION ---
    {
        "codigo": "shock_replacement",
        "categoria": "suspension",
        "nombre_es": "Cambio amortiguadores",
        "nombre_en_oficial": "Shock Replacement",
        "nombre_en_slang": "Shock job",
        "sinonimos_en": [],
        "sinonimos_es": [],
    },
    {
        "codigo": "strut_replacement",
        "categoria": "suspension",
        "nombre_es": "Cambio strut",
        "nombre_en_oficial": "Strut Replacement",
        "nombre_en_slang": "Struts",
        "sinonimos_en": [],
        "sinonimos_es": [],
    },
    {
        "codigo": "control_arm_replacement",
        "categoria": "suspension",
        "nombre_es": "Cambio bandeja suspensión",
        "nombre_en_oficial": "Control Arm Replacement",
        "nombre_en_slang": "Control arm",
        "sinonimos_en": [],
        "sinonimos_es": [],
    },
    {
        "codigo": "sway_bar_link_replacement",
        "categoria": "suspension",
        "nombre_es": "Cambio bieletas",
        "nombre_en_oficial": "Sway Bar Link Replacement",
        "nombre_en_slang": "Sway links",
        "sinonimos_en": [],
        "sinonimos_es": [],
    },
    # --- STEERING ---
    {
        "codigo": "wheel_alignment",
        "categoria": "steering",
        "nombre_es": "Alineación",
        "nombre_en_oficial": "Wheel Alignment",
        "nombre_en_slang": "Alignment",
        "sinonimos_en": [],
        "sinonimos_es": [],
    },
    {
        "codigo": "power_steering_service",
        "categoria": "steering",
        "nombre_es": "Servicio dirección hidráulica",
        "nombre_en_oficial": "Power Steering Service",
        "nombre_en_slang": "Steering service",
        "sinonimos_en": [],
        "sinonimos_es": [],
    },
    {
        "codigo": "tie_rod_replacement",
        "categoria": "steering",
        "nombre_es": "Cambio terminal dirección",
        "nombre_en_oficial": "Tie Rod Replacement",
        "nombre_en_slang": "Tie rod",
        "sinonimos_en": [],
        "sinonimos_es": [],
    },
    # --- COOLING ---
    {
        "codigo": "radiator_replacement",
        "categoria": "cooling",
        "nombre_es": "Cambio radiador",
        "nombre_en_oficial": "Radiator Replacement",
        "nombre_en_slang": "Radiator",
        "sinonimos_en": [],
        "sinonimos_es": [],
    },
    {
        "codigo": "coolant_flush",
        "categoria": "cooling",
        "nombre_es": "Cambio refrigerante",
        "nombre_en_oficial": "Coolant Flush",
        "nombre_en_slang": "Coolant service",
        "sinonimos_en": [],
        "sinonimos_es": [],
    },
    {
        "codigo": "water_pump_replacement",
        "categoria": "cooling",
        "nombre_es": "Cambio bomba agua",
        "nombre_en_oficial": "Water Pump Replacement",
        "nombre_en_slang": "Water pump",
        "sinonimos_en": [],
        "sinonimos_es": [],
    },
    # --- ELECTRICAL ---
    {
        "codigo": "battery_replacement",
        "categoria": "electrical",
        "nombre_es": "Cambio batería",
        "nombre_en_oficial": "Battery Replacement",
        "nombre_en_slang": "Battery",
        "sinonimos_en": [],
        "sinonimos_es": [],
    },
    {
        "codigo": "alternator_replacement",
        "categoria": "electrical",
        "nombre_es": "Cambio alternador",
        "nombre_en_oficial": "Alternator Replacement",
        "nombre_en_slang": "Alternator",
        "sinonimos_en": [],
        "sinonimos_es": [],
    },
    {
        "codigo": "starter_replacement",
        "categoria": "electrical",
        "nombre_es": "Cambio motor arranque",
        "nombre_en_oficial": "Starter Replacement",
        "nombre_en_slang": "Starter",
        "sinonimos_en": [],
        "sinonimos_es": [],
    },
    # --- DIAGNOSTICS ---
    {
        "codigo": "computer_diagnostics",
        "categoria": "diagnostics",
        "nombre_es": "Diagnóstico computacional",
        "nombre_en_oficial": "Computer Diagnostics",
        "nombre_en_slang": "Diagnostics",
        "sinonimos_en": [],
        "sinonimos_es": [],
    },
    {
        "codigo": "check_engine_scan",
        "categoria": "diagnostics",
        "nombre_es": "Escaneo check engine",
        "nombre_en_oficial": "Check Engine Scan",
        "nombre_en_slang": "Engine scan",
        "sinonimos_en": [],
        "sinonimos_es": [],
    },
]


def get_categorias_servicios_usa():
    """Devuelve las categorías únicas del catálogo de servicios USA (ordenadas)."""
    return sorted({s["categoria"] for s in SERVICIOS_AUTOMOTRICES_USA})


def get_servicio_by_codigo(codigo):
    """Devuelve la entrada del catálogo por código o None."""
    for s in SERVICIOS_AUTOMOTRICES_USA:
        if s["codigo"] == codigo:
            return s
    return None


def buscar_servicios_usa(query, lang="en"):
    """
    Búsqueda por texto sobre el catálogo de servicios USA.
    query: término a buscar (minúsculas recomendado).
    lang: 'en' o 'es' para priorizar nombre/sinónimos en ese idioma.
    """
    q = (query or "").strip().lower()
    if not q:
        return []
    results = []
    for s in SERVICIOS_AUTOMOTRICES_USA:
        score = 0
        if q in (s.get("codigo") or "").lower():
            score += 10
        if q in (s.get("nombre_en_oficial") or "").lower():
            score += 5
        if q in (s.get("nombre_en_slang") or "").lower():
            score += 4
        if q in (s.get("nombre_es") or "").lower():
            score += 5
        if q in (s.get("categoria") or "").lower():
            score += 2
        for syn in s.get("sinonimos_en") or []:
            if q in syn.lower():
                score += 3
                break
        for syn in s.get("sinonimos_es") or []:
            if q in syn.lower():
                score += 3
                break
        if score > 0:
            results.append((score, s))
    results.sort(key=lambda x: -x[0])
    return [s for _, s in results]
