# Helpers centralizados para Django Autocomplete Light (DAL)
from typing import Optional


def get_dal_namespace(country: Optional[str]) -> str:
    """
    Helper centralizado para generar namespaces de DAL según el país.

    Args:
        country: Código de país ("US", "CL", etc.)

    Returns:
        Namespace apropiado para DAL autocomplete

    Examples:
        >>> get_dal_namespace("US")
        'usa_autocomplete'
        >>> get_dal_namespace("CL")
        'cl_autocomplete'
        >>> get_dal_namespace(None)
        'cl_autocomplete'
    """
    if (country or "").upper() == "US":
        return "usa_autocomplete"
    return "cl_autocomplete"


def get_autocomplete_url(country: Optional[str], target: str) -> str:
    """
    Helper para generar URLs completas de autocompletado según el país.

    Args:
        country: Código de país ("US", "CL", etc.)
        target: Target del autocomplete ("cliente", "vehiculo", etc.)

    Returns:
        URL completa para el widget DAL

    Examples:
        >>> get_autocomplete_url("US", "cliente")
        'usa_autocomplete:cliente'
        >>> get_autocomplete_url("CL", "vehiculo")
        'cl_autocomplete:vehiculo'
    """
    namespace = get_dal_namespace(country)
    return f"{namespace}:{target}"


def get_document_prefix(tipo: str) -> str:
    """
    Helper para obtener prefijos de numeración de documentos.

    Args:
        tipo: Tipo de documento ("OT", "PRES", "REC", "FAC")

    Returns:
        Prefijo para numeración

    Examples:
        >>> get_document_prefix("OT")
        'OT'
        >>> get_document_prefix("REC")
        'R'
        >>> get_document_prefix("PRES")
        'P'
    """
    prefixes = {"OT": "OT", "FAC": "F", "PRES": "P", "REC": "R"}
    return prefixes.get(tipo, "D")


def get_template_by_country(country: Optional[str], template_path: str) -> str:
    """
    Helper para generar rutas de templates según el país.

    Args:
        country: Código de país ("US", "CL", etc.)
        template_path: Ruta base del template

    Returns:
        Ruta completa del template según el país

    Examples:
        >>> get_template_by_country("US", "documentos/crear_documento.html")
        'taller/us/en/documentos/crear_documento.html'
        >>> get_template_by_country("CL", "documentos/crear_documento.html")
        'taller/cl/es/documentos/crear_documento.html'
    """
    if (country or "").upper() == "US":
        return f"taller/us/en/{template_path}"
    return f"taller/cl/es/{template_path}"
