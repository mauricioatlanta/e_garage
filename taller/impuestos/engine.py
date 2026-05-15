# -*- coding: utf-8 -*-
"""
Motor de cálculo de impuestos multi-país

Convenciones del proyecto:
- Chile: IVA 19% solo a repuestos (no servicios)
- USA: sales tax por ubicación (estado/ciudad)
- Brasil: ICMS 18% solo repuestos
- Perú: IGV 18% ambos (repuestos y servicios)
- Venezuela: IVA 16% ambos (repuestos y servicios)
"""
from decimal import Decimal
from typing import Optional, Tuple

from taller.models import TaxPolicy
from taller.models.ubicacion import Ciudad


def resolve_tax_rate(
    empresa, ship_to_city: Optional[Ciudad] = None, applies_to: str = "parts"
) -> Tuple[Decimal, bool]:
    """
    Resuelve la tasa de impuesto aplicable según empresa y ubicación.

    Args:
        empresa: Instancia de Empresa
        ship_to_city: Ciudad de destino (opcional, para granularidad por ubicación)
        applies_to: 'parts' o 'services'

    Returns:
        Tuple[Decimal, bool]: (tasa_impuesto, es_inclusivo)
            - tasa_impuesto: Tasa como decimal (0.19 para 19%)
            - es_inclusivo: True si el impuesto está incluido en el precio

    Ejemplos:
        >>> resolve_tax_rate(empresa_chile, ciudad_santiago, 'parts')
        (Decimal('0.19'), False)  # IVA 19% no incluido

        >>> resolve_tax_rate(empresa_chile, ciudad_santiago, 'services')
        (Decimal('0.00'), False)  # Sin impuesto en servicios Chile

        >>> resolve_tax_rate(empresa_peru, ciudad_lima, 'parts')
        (Decimal('0.18'), False)  # IGV 18% no incluido

    Lógica de Prioridad:
        1. TaxPolicy específica por ciudad (si existe)
        2. TaxPolicy específica por estado (si existe)
        3. TaxPolicy general del país
        4. Sales tax desde Address.city (si ship_to_city existe)
        5. Fallback: 0% sin impuesto
    """

    # Validar empresa
    if not empresa or not hasattr(empresa, "pais"):
        return (Decimal("0.00"), False)

    pais = empresa.pais

    # === ESTRATEGIA 1: TaxPolicy (configuración manual más específica) ===

    # Si hay ciudad de destino, buscar política por ciudad
    if ship_to_city and ship_to_city.estado:
        state_code = getattr(ship_to_city.estado, "codigo", "") or ""
        city_name = ship_to_city.nombre

        # 1a. Política específica por ciudad
        policy = (
            TaxPolicy.objects.filter(
                country=pais, state_code=state_code, city_name=city_name, active=True
            )
            .filter(models.Q(applies_to=applies_to) | models.Q(applies_to="both"))
            .first()
        )

        if policy:
            return (policy.rate, policy.inclusive)

        # 1b. Política específica por estado
        policy = (
            TaxPolicy.objects.filter(
                country=pais,
                state_code=state_code,
                city_name="",  # Sin ciudad específica
                active=True,
            )
            .filter(models.Q(applies_to=applies_to) | models.Q(applies_to="both"))
            .first()
        )

        if policy:
            return (policy.rate, policy.inclusive)

    # 1c. Política general del país
    policy = (
        TaxPolicy.objects.filter(country=pais, state_code="", city_name="", active=True)
        .filter(models.Q(applies_to=applies_to) | models.Q(applies_to="both"))
        .first()
    )

    if policy:
        return (policy.rate, policy.inclusive)

    # === ESTRATEGIA 2: Sales tax desde Address/Ciudad (fallback automático) ===

    if ship_to_city:
        # Usar sales_tax_total de la ciudad (estado + ciudad)
        sales_tax_total = ship_to_city.sales_tax_total

        # CONVENCIÓN: Chile no cobra IVA en servicios
        if pais == "CL" and applies_to == "services":
            return (Decimal("0.00"), False)

        # Retornar sales tax de la ciudad/estado
        return (sales_tax_total / 100, False)  # Convertir % a decimal

    # === ESTRATEGIA 3: Fallback por país (hardcoded - último recurso) ===

    # Tasas por defecto según convenciones del proyecto
    DEFAULT_RATES = {
        "CL": {
            "parts": Decimal("0.1900"),  # IVA 19% solo repuestos
            "services": Decimal("0.0000"),  # Sin IVA en servicios
        },
        "US": {
            "parts": Decimal("0.0000"),  # Varía por estado/ciudad
            "services": Decimal("0.0000"),  # Varía por estado/ciudad
        },
        "BR": {
            "parts": Decimal("0.1800"),  # ICMS 18% repuestos
            "services": Decimal("0.0000"),  # Sin ISS en servicios (simplificado)
        },
        "PE": {
            "parts": Decimal("0.1800"),  # IGV 18% ambos
            "services": Decimal("0.1800"),  # IGV 18% ambos
        },
        "VE": {
            "parts": Decimal("0.1600"),  # IVA 16% ambos
            "services": Decimal("0.1600"),  # IVA 16% ambos
        },
    }

    if pais in DEFAULT_RATES:
        rate = DEFAULT_RATES[pais].get(applies_to, Decimal("0.00"))
        return (rate, False)

    # Último fallback: sin impuesto
    return (Decimal("0.00"), False)


def get_tax_info(empresa, ship_to_city: Optional[Ciudad] = None, applies_to: str = "parts") -> dict:
    """
    Obtiene información detallada sobre el impuesto aplicable.

    Args:
        empresa: Instancia de Empresa
        ship_to_city: Ciudad de destino (opcional)
        applies_to: 'parts' o 'services'

    Returns:
        dict con información del impuesto:
            - rate: Tasa como decimal (0.19)
            - rate_percentage: Tasa como porcentaje (19.0)
            - inclusive: Si está incluido en precio
            - name: Nombre del impuesto (IVA, Sales Tax, IGV, etc.)
            - country: Código de país
            - state: Nombre de estado (si aplica)
            - city: Nombre de ciudad (si aplica)

    Ejemplo:
        >>> info = get_tax_info(empresa_chile, ciudad_santiago, 'parts')
        >>> print(info)
        {
            'rate': Decimal('0.19'),
            'rate_percentage': 19.0,
            'inclusive': False,
            'name': 'IVA',
            'country': 'CL',
            'state': 'Región Metropolitana',
            'city': 'Santiago'
        }
    """
    rate, inclusive = resolve_tax_rate(empresa, ship_to_city, applies_to)

    # Nombres de impuestos por país
    TAX_NAMES = {
        "CL": "IVA",
        "US": "Sales Tax",
        "BR": "ICMS" if applies_to == "parts" else "ISS",
        "PE": "IGV",
        "VE": "IVA",
    }

    pais = empresa.pais if empresa else "CL"

    info = {
        "rate": rate,
        "rate_percentage": float(rate * 100),
        "inclusive": inclusive,
        "name": TAX_NAMES.get(pais, "Tax"),
        "country": pais,
        "state": None,
        "city": None,
    }

    # Agregar info de ubicación si existe
    if ship_to_city:
        info["city"] = ship_to_city.nombre
        if ship_to_city.estado:
            info["state"] = ship_to_city.estado.nombre

    return info


# Import necesario para Q lookups
from django.db import models


def calcular_impuesto(base: Decimal, empresa, applies_to: str = "parts") -> Decimal:
    """
    Función centralizada para calcular impuesto sobre una base según configuración del tenant.

    Esta es la función principal que debe usarse en todo el código para calcular impuestos,
    reemplazando las múltiples instancias de if/else dispersas.

    Args:
        base: Base imponible (Decimal o número)
        empresa: Instancia de Empresa (tenant)
        applies_to: 'parts' (repuestos) o 'services' (servicios)

    Returns:
        Decimal: Monto del impuesto calculado

    Ejemplo:
        >>> from decimal import Decimal
        >>> base = Decimal("1000.00")
        >>> impuesto = calcular_impuesto(base, empresa_chile, 'parts')
        >>> print(impuesto)  # Decimal('190.00') para IVA 19%

    Uso recomendado:
        En lugar de:
            if empresa.pais == "CL":
                tax = base * Decimal("0.19")
            elif empresa.pais == "US":
                tax = Decimal("0.00")

        Usar:
            tax = calcular_impuesto(base, empresa, 'parts')
    """
    if base is None:
        base = Decimal("0.00")

    if not isinstance(base, Decimal):
        base = Decimal(str(base))

    # Obtener tasa usando la función existente
    rate, _ = resolve_tax_rate(empresa, ship_to_city=None, applies_to=applies_to)

    # Calcular impuesto
    impuesto = base * rate

    return impuesto.quantize(Decimal("0.01"))


def get_tax_rate_simple(empresa, applies_to: str = "parts") -> Decimal:
    """
    Obtiene la tasa de impuesto como decimal (0.19 para 19%) de forma simple.

    Esta es una función helper que retorna solo la tasa sin información adicional.

    Args:
        empresa: Instancia de Empresa
        applies_to: 'parts' o 'services'

    Returns:
        Decimal: Tasa de impuesto (ej: Decimal('0.19') para 19%)

    Ejemplo:
        >>> tasa = get_tax_rate_simple(empresa_chile, 'parts')
        >>> print(tasa)  # Decimal('0.19')
    """
    rate, _ = resolve_tax_rate(empresa, ship_to_city=None, applies_to=applies_to)
    return rate
