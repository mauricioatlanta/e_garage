"""
Utilidades para detección automática de garantías en el flujo de creación de documentos.
"""

from typing import Dict, Optional

from taller.models import Documento
from taller.reportes.kilometraje_reportes import ReporteKilometraje


def detectar_garantia_automatica(documento: Documento) -> Optional[Dict]:
    """
    Detecta automáticamente si un documento nuevo podría ser una garantía
    basándose en el vehículo y documentos anteriores.

    Args:
        documento: Documento recién creado o en proceso de creación

    Returns:
        dict con información de garantía detectada, o None si no se detecta
    """
    if not documento.vehiculo or not documento.empresa:
        return None

    # Buscar documentos anteriores del mismo vehículo
    documentos_anteriores = (
        Documento.objects.filter(
            empresa=documento.empresa,
            vehiculo=documento.vehiculo,
            tipo__in=["OT", "PRES"],
            fecha_emision__lt=documento.fecha_emision,
            estado="EMITIDO",
        )
        .select_related("registro_kilometraje")
        .order_by("-fecha_emision")[:5]
    )

    if not documentos_anteriores:
        return None

    # Verificar si el documento actual tiene registro de kilometraje
    if not hasattr(documento, "registro_kilometraje") or not documento.registro_kilometraje:
        return None

    reporte = ReporteKilometraje(documento.empresa)
    garantias_detectadas = []

    # Verificar contra cada documento anterior
    for doc_anterior in documentos_anteriores:
        if (
            not hasattr(doc_anterior, "registro_kilometraje")
            or not doc_anterior.registro_kilometraje
        ):
            continue

        try:
            verificacion = reporte.verificar_garantia(documento, doc_anterior)
            if verificacion and not verificacion.get("error"):
                garantias_detectadas.append(
                    {"documento_original": doc_anterior, "verificacion": verificacion}
                )
        except Exception:
            continue

    if not garantias_detectadas:
        return None

    # Retornar la garantía más reciente (primera en la lista)
    garantia_principal = garantias_detectadas[0]

    return {
        "detectada": True,
        "documento_original": garantia_principal["documento_original"],
        "verificacion": garantia_principal["verificacion"],
        "todas_las_garantias": garantias_detectadas,
    }


def obtener_contexto_garantia(documento: Documento) -> Dict:
    """
    Obtiene el contexto de garantía para incluir en las vistas de creación/edición.

    Args:
        documento: Documento (puede ser nuevo o existente)

    Returns:
        dict con información de garantía para el contexto
    """
    garantia_info = detectar_garantia_automatica(documento)

    if not garantia_info:
        return {"garantia_detectada": False, "mostrar_alerta_garantia": False}

    verificacion = garantia_info["verificacion"]

    return {
        "garantia_detectada": True,
        "mostrar_alerta_garantia": True,
        "documento_original": garantia_info["documento_original"],
        "dentro_garantia": verificacion.get("dentro_garantia", False),
        "kilometros_recorridos": verificacion.get("kilometros_recorridos"),
        "limite_garantia_km": verificacion.get("limite_garantia_km", 5000),
        "porcentaje_uso": verificacion.get("porcentaje_uso", 0),
        "mensaje_garantia": verificacion.get("mensaje", ""),
        "verificacion_completa": verificacion,
    }
