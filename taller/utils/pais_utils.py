"""
Utilidades para manejo de países y localización
"""

MEXICO_ESTADOS = [
    ("AG", "Aguascalientes"),
    ("BC", "Baja California"),
    ("BS", "Baja California Sur"),
    ("CM", "Campeche"),
    ("CO", "Coahuila"),
    ("CL", "Colima"),
    ("CS", "Chiapas"),
    ("CH", "Chihuahua"),
    ("CX", "Ciudad de México"),
    ("DG", "Durango"),
    ("GT", "Guanajuato"),
    ("GR", "Guerrero"),
    ("HG", "Hidalgo"),
    ("JA", "Jalisco"),
    ("ME", "Estado de México"),
    ("MI", "Michoacán"),
    ("MO", "Morelos"),
    ("NA", "Nayarit"),
    ("NL", "Nuevo León"),
    ("OA", "Oaxaca"),
    ("PU", "Puebla"),
    ("QE", "Querétaro"),
    ("QR", "Quintana Roo"),
    ("SL", "San Luis Potosí"),
    ("SI", "Sinaloa"),
    ("SO", "Sonora"),
    ("TB", "Tabasco"),
    ("TM", "Tamaulipas"),
    ("TL", "Tlaxcala"),
    ("VE", "Veracruz"),
    ("YU", "Yucatán"),
    ("ZA", "Zacatecas"),
]


def get_marcas_por_pais(user):
    """
    Retorna las marcas de vehículos según el país del usuario
    """
    pais = getattr(getattr(user, "empresa", None), "pais", None)
    if pais == "US":
        from taller.models.marcas_usa import MarcaVehiculo

        return MarcaVehiculo.objects.filter(pais_origen="USA", activa=True)

    from taller.models.marca import Marca

    if pais == "MX":
        return Marca.objects.filter(country__in=["MX", "CL"]).order_by("nombre")

    return Marca.objects.filter(country__in=["CL", "MX"]).order_by("nombre")


def get_configuracion_pais(empresa):
    """
    Retorna configuración específica según el país de la empresa.

    Usa configuración centralizada de country_config.py.

    Args:
        empresa: Instancia de modelo Empresa

    Returns:
        dict: Configuración completa del país
    """
    from taller.utils.country_config import get_config_from_empresa

    config = get_config_from_empresa(empresa)
    pais = getattr(empresa, "pais", "CL")

    # Validaciones de patente por país (mantener lógica específica)
    validacion_patente_map = {
        "US": r"^[A-Z0-9]{2,7}$",  # Formato USA más flexible
        "MX": r"^[A-Z]{3}\d{3,4}$",  # Formato general México
        "CL": r"^[A-Z]{2}\d{4}$",  # Formato Chile: AA1234
        "PE": r"^[A-Z]{3}\d{3}$",  # Formato Perú: ABC123
        "CO": r"^[A-Z]{3}\d{3}[A-Z]?$",  # Formato Colombia
        "EC": r"^[A-Z]{3}\d{4}$",  # Formato Ecuador
        "BR": r"^[A-Z]{3}\d{4}$",  # Formato Brasil
        "VE": r"^[A-Z]{3}\d{3}$",  # Formato Venezuela
    }

    # Construir respuesta con configuración centralizada
    result = {
        "moneda": config["currency"],
        "simbolo_moneda": config["currency_symbol"],
        "decimales": config["decimals"],
        "idioma_default": config["lang"],
        "formato_fecha": config["date_format"],
        "zona_horaria_default": config["timezone"],
        "validacion_patente": validacion_patente_map.get(pais, r"^[A-Z]{2,4}\d{2,4}$"),
        "impuesto_default": config["tax_rate"] / 100.0,  # Convertir de porcentaje a decimal
    }

    return result


def formatear_precio(precio, empresa):
    """
    Formatea el precio según el país de la empresa
    """
    config = get_configuracion_pais(empresa)

    if config["decimales"] > 0:
        return f"{config['simbolo_moneda']}{precio:.{config['decimales']}f} {config['moneda']}"
    else:
        return f"{config['simbolo_moneda']}{precio:,.0f} {config['moneda']}"


def get_modelos_por_marca_y_pais(marca_id, user):
    """
    Retorna modelos filtrados por marca y país del usuario
    """
    pais = getattr(getattr(user, "empresa", None), "pais", "CL")
    if pais == "US":
        # Para USA, usar el sistema de MarcaVehiculo (si existe ModeloVehiculo)
        try:
            from taller.models.marcas_usa import ModeloVehiculo

            return ModeloVehiculo.objects.filter(marca_id=marca_id, activo=True)
        except ImportError:
            # Si no existe ModeloVehiculo, usar el sistema tradicional
            from taller.models.modelo import Modelo

            return Modelo.objects.filter(marca_id=marca_id)
    # Para Chile, México y otros, usar el sistema tradicional
    from taller.models.modelo import Modelo

    filtros = {"marca_id": marca_id}
    if pais in ("CL", "MX"):
        filtros["country"] = pais
    return Modelo.objects.filter(**filtros)


def validar_patente_por_pais(patente, pais):
    """
    Valida formato de patente según el país
    """
    import re

    if pais == "US":
        # USA: formatos variados por estado, más flexible
        return bool(re.match(r"^[A-Z0-9]{2,8}$", patente.upper()))
    if pais == "MX":
        # México: AAA1234 o AAA123
        return bool(re.match(r"^[A-Z]{3}\d{3,4}$", patente.upper()))
    else:
        # Chile: formato AA1234 o ABCD12
        return bool(re.match(r"^[A-Z]{2,4}\d{2,4}$", patente.upper()))


def get_regiones_por_pais(pais):
    """
    Retorna regiones/estados según el país
    """
    if pais == "US":
        # Estados de USA
        return [
            ("AL", "Alabama"),
            ("AK", "Alaska"),
            ("AZ", "Arizona"),
            ("AR", "Arkansas"),
            ("CA", "California"),
            ("CO", "Colorado"),
            ("CT", "Connecticut"),
            ("DE", "Delaware"),
            ("FL", "Florida"),
            ("GA", "Georgia"),
            ("HI", "Hawaii"),
            ("ID", "Idaho"),
            ("IL", "Illinois"),
            ("IN", "Indiana"),
            ("IA", "Iowa"),
            ("KS", "Kansas"),
            ("KY", "Kentucky"),
            ("LA", "Louisiana"),
            ("ME", "Maine"),
            ("MD", "Maryland"),
            ("MA", "Massachusetts"),
            ("MI", "Michigan"),
            ("MN", "Minnesota"),
            ("MS", "Mississippi"),
            ("MO", "Missouri"),
            ("MT", "Montana"),
            ("NE", "Nebraska"),
            ("NV", "Nevada"),
            ("NH", "New Hampshire"),
            ("NJ", "New Jersey"),
            ("NM", "New Mexico"),
            ("NY", "New York"),
            ("NC", "North Carolina"),
            ("ND", "North Dakota"),
            ("OH", "Ohio"),
            ("OK", "Oklahoma"),
            ("OR", "Oregon"),
            ("PA", "Pennsylvania"),
            ("RI", "Rhode Island"),
            ("SC", "South Carolina"),
            ("SD", "South Dakota"),
            ("TN", "Tennessee"),
            ("TX", "Texas"),
            ("UT", "Utah"),
            ("VT", "Vermont"),
            ("VA", "Virginia"),
            ("WA", "Washington"),
            ("WV", "West Virginia"),
            ("WI", "Wisconsin"),
            ("WY", "Wyoming"),
        ]
    if pais == "MX":
        return MEXICO_ESTADOS

    else:
        # Regiones de Chile
        from taller.models.region_ciudad import TallerRegion

        return [(str(r.pk), r.nombre) for r in TallerRegion.objects.all()]


def validar_telefono_por_pais(telefono, pais):
    """
    Valida formato de teléfono según el país
    """
    import re

    normalizado = telefono.replace(" ", "").replace("-", "")

    if pais == "US":
        # USA: (123) 456-7890 o 123-456-7890 o 1234567890
        patron = r"^(\+1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}$"
        return bool(re.match(patron, telefono))
    if pais == "MX":
        # México: +52 55 1234 5678 o 5512345678
        patron = r"^(\+52)?\d{10}$"
        return bool(re.match(patron, normalizado))
    else:
        # Chile: +56912345678 o 912345678 o 22345678
        patron = r"^(\+56)?[0-9]{8,9}$"
        return bool(re.match(patron, normalizado))
