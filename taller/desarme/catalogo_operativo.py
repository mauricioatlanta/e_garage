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
        nombre = p.get("nombre_en_oficial") or p.get("nombre_en_slang") or p.get("nombre_es") or p.get("codigo", "")
        out.append({
            "codigo": p.get("codigo", ""),
            "nombre": nombre,
            "zona": zona,
            "precio_base": Decimal("0"),
        })
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
