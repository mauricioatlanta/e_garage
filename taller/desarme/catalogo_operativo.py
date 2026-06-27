"""
Adaptador operativo de catálogos de desarme.
Unifica legacy (CL/MX) y USA en un contrato común: codigo, nombre, zona, precio_base.
Para Fase 1: empresa USA usa catálogo USA; resto usa catálogo legacy.
"""

from decimal import Decimal

# Mapeo categoría USA → zona mostrada en scanner (compatible con UI actual)
USA_CATEGORIA_TO_ZONA = {
    "engine": "Motor",
    "drivetrain": "Transmisión",
    "suspension": "Suspensión",
    "brakes": "Frenos",
    "cooling": "Cooling",
    "electrical": "Electrónica",
    "body": "Carrocería",
}

# Orden de zonas para scanner USA (valores de USA_CATEGORIA_TO_ZONA)
ZONAS_ORDEN_USA = [
    "Motor",
    "Transmisión",
    "Suspensión",
    "Frenos",
    "Cooling",
    "Electrónica",
    "Carrocería",
]


def _is_empresa_usa(empresa):
    """True si la empresa es mercado USA (pais US)."""
    if not empresa:
        return False
    pais = getattr(empresa, "pais", None)
    if pais is None:
        return False
    return str(pais).upper().strip() == "US"


def _catalogo_legacy_a_operativo():
    """Convierte CATALOGO_PIEZAS (tuplas) a lista de dicts operativos."""
    from .catalogo_piezas import CATALOGO_PIEZAS

    return [
        {
            "codigo": codigo,
            "nombre": nombre,
            "zona": zona,
            "precio_base": precio_base,
        }
        for codigo, nombre, zona, precio_base in CATALOGO_PIEZAS
    ]


def _catalogo_usa_a_operativo():
    """Convierte catálogo USA a lista de dicts operativos (nombre_en_oficial, zona mapeada, precio_base=0)."""
    from taller.catalogos.catalogo_piezas_desarme_usa import CATALOGO_PIEZAS_DESARME_USA

    out = []
    for p in CATALOGO_PIEZAS_DESARME_USA:
        categoria = p.get("categoria") or ""
        zona = USA_CATEGORIA_TO_ZONA.get(categoria, categoria or "Otros")
        nombre = (
            p.get("nombre_en_oficial")
            or p.get("nombre_en_slang")
            or p.get("nombre_es")
            or p.get("codigo", "")
        )
        out.append(
            {
                "codigo": p.get("codigo", ""),
                "nombre": nombre,
                "zona": zona,
                "precio_base": Decimal("0"),
            }
        )
    return out


def get_catalogo_operativo_desarme(empresa):
    """
    Devuelve el catálogo de piezas en formato operativo homogéneo para el generador de inventario.
    Cada item es un dict: {"codigo", "nombre", "zona", "precio_base"}.
    - Empresa USA (pais='US') → catálogo USA (engine_assembly, alternator, hood, etc.).
    - Resto (CL, MX, etc.) → catálogo legacy (MOT-01, CAR-01, etc.).
    """
    if _is_empresa_usa(empresa):
        return _catalogo_usa_a_operativo()
    return _catalogo_legacy_a_operativo()


def get_zonas_orden_desarme(empresa):
    """
    Devuelve el orden de zonas para el scanner según el país de la empresa.
    - USA → ZONAS_ORDEN_USA.
    - Resto → ZONAS_ORDEN legacy (Motor, Carrocería, Interior, ...).
    - Fallback → orden alfabético de las zonas presentes.
    """
    from .catalogo_piezas import ZONAS_ORDEN

    if _is_empresa_usa(empresa):
        return list(ZONAS_ORDEN_USA)
    return list(ZONAS_ORDEN)


# ── Catálogo por tipo de carrocería ──────────────────────────────────────────

# Piezas excluidas del catálogo base según tipo de carrocería.
# Clave: valor de Vehiculo.tipo_carroceria. Valor: frozenset de códigos excluidos.
EXCLUSIONES_POR_CARROCERIA: dict = {
    "sedan": frozenset({
        "CAR-12",                        # Puerta maletero — sedán tiene tapa baúl (CAR-07)
    }),
    "hatchback": frozenset({
        "CAR-07",                        # Tapa baúl — hatchback tiene compuerta (CAR-12)
    }),
    "suv": frozenset({
        "CAR-07",
    }),
    "crossover": frozenset({
        "CAR-07",
    }),
    "station_wagon": frozenset({
        "CAR-07",
    }),
    "coupe": frozenset({
        "CAR-04", "CAR-05",             # Sin puertas traseras
        "CAR-07",                        # Sin tapa baúl clásica
        "CAR-12",                        # Sin compuerta
        "ELE-07", "ELE-08",             # Sin vidrios puerta trasera
    }),
    "pickup": frozenset({
        "CAR-04", "CAR-05",             # Cab simple: sin puertas traseras
        "CAR-06",                        # Sin baguetera
        "CAR-07",                        # Caja abierta, no baúl
        "CAR-12",                        # Sin compuerta
        "ELE-07", "ELE-08",             # Sin vidrios puerta trasera
        "INT-03",                        # Sin asiento trasero
    }),
    "camion": frozenset({
        "CAR-04", "CAR-05",
        "CAR-06", "CAR-07", "CAR-12",
        "ELE-07", "ELE-08", "ELE-09", "ELE-10",
        "INT-03",
    }),
    "minivan": frozenset({
        "CAR-07",
    }),
    "van": frozenset({
        "CAR-07",
    }),
    "utilitario": frozenset({
        "CAR-07", "CAR-12",
    }),
    "convertible": frozenset({
        "CAR-07",
    }),
    "compacto": frozenset({
        "CAR-12",
    }),
    # "otro" y None → catálogo completo (no está en el dict → sin exclusiones)
}

# Whitelist para motos: el catálogo base es tan distinto que es más claro listar lo que SÍ aplica.
CODIGOS_MOTO_WHITELIST: frozenset = frozenset({
    # Motor
    "MOT-01", "MOT-02", "MOT-03", "MOT-06", "MOT-07", "MOT-08", "MOT-14", "MOT-15",
    # Suspensión (horquillas y amortiguadores, sin barra estabilizadora ni cremallera)
    "SUS-01", "SUS-02", "SUS-03", "SUS-04",
    # Iluminación básica
    "ILU-01", "ILU-02", "ILU-03", "ILU-04", "ILU-08", "ILU-09", "ILU-10",
    # Electrónica básica
    "ELE-03", "ELE-14",
    # Escape
    "ESC-01", "ESC-02", "ESC-03",
    # Ruedas
    "RUE-01", "RUE-04", "RUE-09",
})


def get_catalogo_para_vehiculo(empresa, vehiculo) -> list:
    """
    Catálogo sugerido filtrado por tipo_carroceria del vehículo.
    Fallback a catálogo genérico si tipo es null, vacío o no reconocido.
    """
    base = get_catalogo_operativo_desarme(empresa)
    tipo = (getattr(vehiculo, "tipo_carroceria", None) or "").lower().strip()

    if tipo == "moto":
        return [item for item in base if item["codigo"] in CODIGOS_MOTO_WHITELIST]

    excluidos = EXCLUSIONES_POR_CARROCERIA.get(tipo, frozenset())
    return [item for item in base if item["codigo"] not in excluidos]
