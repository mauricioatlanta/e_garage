"""
Utilidades para validación de facturación y exportación CSV SII.

Este módulo proporciona funciones helper para validar que los clientes
tengan todos los datos necesarios antes de exportar para facturación.
"""
from typing import List, Dict, Any, Optional

from taller.models.clientes import Cliente
from taller.models.documento import Documento


def validar_cliente_para_facturacion(cliente: Cliente) -> Dict[str, Any]:
    """
    Valida si un cliente está listo para facturación.
    
    Args:
        cliente: Instancia del modelo Cliente
        
    Returns:
        dict con:
            - is_ready: bool - Si el cliente está listo
            - missing_fields: list - Campos faltantes
            - can_export: bool - Si se puede exportar CSV
            - message: str - Mensaje para mostrar al usuario
    """
    is_ready = cliente.is_billing_ready()
    missing = cliente.get_missing_billing_fields()
    profile_status = cliente.get_profile_status()
    
    return {
        "is_ready": is_ready,
        "missing_fields": missing,
        "can_export": is_ready,
        "message": (
            f"El cliente '{cliente.nombre}' está listo para facturar."
            if is_ready
            else f"Para facturar a este cliente, completa estos campos: {', '.join(missing)}"
        ),
        "profile_status": profile_status,
    }


def validar_documentos_para_exportacion_sii(
    documentos: List[Documento],
    empresa_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Valida que todos los documentos tengan clientes listos para facturación.
    
    Útil antes de exportar un CSV para SII o generar facturas masivas.
    
    Args:
        documentos: Lista de documentos a validar
        empresa_id: ID de empresa (opcional, para filtrado adicional)
        
    Returns:
        dict con:
            - all_ready: bool - Si todos los clientes están listos
            - total_documentos: int - Total de documentos
            - documentos_con_problemas: list - Documentos con clientes incompletos
            - clientes_incompletos: list - Clientes que faltan datos
            - can_export: bool - Si se puede exportar
            - message: str - Mensaje para mostrar
    """
    documentos_con_problemas = []
    clientes_incompletos = {}
    
    for doc in documentos:
        if not doc.cliente:
            documentos_con_problemas.append({
                "documento_id": doc.id,
                "numero": doc.numero_documento or f"Doc #{doc.id}",
                "problema": "Sin cliente asignado",
            })
            continue
        
        cliente = doc.cliente
        validacion = validar_cliente_para_facturacion(cliente)
        
        if not validacion["is_ready"]:
            documentos_con_problemas.append({
                "documento_id": doc.id,
                "numero": doc.numero_documento or f"Doc #{doc.id}",
                "cliente_id": cliente.id,
                "cliente_nombre": str(cliente),
                "problema": "Cliente sin datos de facturación completos",
                "missing_fields": validacion["missing_fields"],
            })
            
            # Agregar a clientes incompletos (evitar duplicados)
            if cliente.id not in clientes_incompletos:
                clientes_incompletos[cliente.id] = {
                    "cliente_id": cliente.id,
                    "cliente_nombre": str(cliente),
                    "missing_fields": validacion["missing_fields"],
                    "profile_status": validacion["profile_status"],
                }
    
    all_ready = len(documentos_con_problemas) == 0
    
    return {
        "all_ready": all_ready,
        "total_documentos": len(documentos),
        "documentos_con_problemas": documentos_con_problemas,
        "clientes_incompletos": list(clientes_incompletos.values()),
        "can_export": all_ready,
        "message": (
            f"✅ Todos los clientes ({len(documentos)} documentos) están listos para exportar."
            if all_ready
            else f"⚠️ {len(documentos_con_problemas)} documento(s) tienen clientes con datos incompletos. "
                 f"Completa los datos de facturación antes de exportar."
        ),
    }


def generar_csv_sii_validado(
    documentos: List[Documento],
    empresa_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Genera CSV para SII con validación previa.
    
    Si hay clientes incompletos, retorna información para guiar al usuario
    en lugar de generar el CSV.
    
    Args:
        documentos: Lista de documentos a exportar
        empresa_id: ID de empresa (opcional)
        
    Returns:
        dict con:
            - success: bool - Si se generó el CSV
            - csv_content: str - Contenido del CSV (si success=True)
            - validation: dict - Resultado de la validación
            - error: str - Mensaje de error (si success=False)
    """
    import csv
    from io import StringIO
    
    # Validar primero
    validacion = validar_documentos_para_exportacion_sii(documentos, empresa_id)
    
    if not validacion["can_export"]:
        return {
            "success": False,
            "csv_content": None,
            "validation": validacion,
            "error": validacion["message"],
        }
    
    # Generar CSV (formato básico - ajustar según requerimientos SII)
    output = StringIO()
    writer = csv.writer(output)
    
    # Encabezados (ajustar según formato SII requerido)
    writer.writerow([
        "Fecha",
        "Tipo Documento",
        "Número Documento",
        "Cliente",
        "RUT/TAX_ID",
        "Giro",
        "Dirección",
        "Total",
    ])
    
    # Filas de datos
    for doc in documentos:
        cliente = doc.cliente
        direccion = ""
        
        if cliente.billing_address:
            direccion = cliente.billing_address.full_address
        elif cliente.ciudad:
            direccion = f"{cliente.direccion or ''}, {cliente.ciudad.nombre}".strip()
        elif cliente.ciudad_usa:
            direccion = f"{cliente.direccion or ''}, {cliente.ciudad_usa.nombre}".strip()
        
        # Calcular total (ajustar según tu lógica)
        total = 0  # TODO: Calcular total del documento
        
        writer.writerow([
            doc.fecha.strftime("%d/%m/%Y") if doc.fecha else "",
            doc.tipo_documento or "",
            doc.numero_documento or "",
            str(cliente),
            cliente.tax_id or "",
            cliente.giro or "",
            direccion,
            total,
        ])
    
    return {
        "success": True,
        "csv_content": output.getvalue(),
        "validation": validacion,
        "error": None,
    }
