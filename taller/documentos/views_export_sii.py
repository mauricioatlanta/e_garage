"""
Vistas para exportación de documentos a formato SII (Chile).
Incluye validación de datos de facturación del cliente.
"""
import csv
from datetime import datetime
from io import StringIO

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods

from taller.models.documento import Documento
from taller.utils.billing_validation import validar_cliente_para_facturacion


@login_required
@require_http_methods(["GET", "POST"])
def exportar_csv_sii(request, documento_id):
    """
    Exporta un documento a CSV compatible con SII.
    
    Si el cliente no tiene todos los datos de facturación:
    - GET: Retorna JSON con campos faltantes
    - POST: Intenta completar datos y luego exportar
    
    GET /documentos/<id>/exportar-sii/
    POST /documentos/<id>/exportar-sii/ (con datos de facturación)
    """
    empresa = getattr(request.user, "empresa", None)
    if not empresa:
        return JsonResponse({"success": False, "error": "No empresa found"}, status=400)
    
    documento = get_object_or_404(Documento, id=documento_id, empresa=empresa)
    
    if not documento.cliente:
        return JsonResponse({
            "success": False,
            "error": "El documento no tiene cliente asignado"
        }, status=400)
    
    cliente = documento.cliente
    
    # Si es POST, intentar completar datos primero
    if request.method == "POST":
        from taller.clientes.forms_unified import BillingDataForm
        
        form = BillingDataForm(request.POST, instance=cliente, empresa=empresa)
        
        if form.is_valid():
            cliente = form.save()
        else:
            # Retornar errores del formulario
            errors = {}
            for field, field_errors in form.errors.items():
                errors[field] = [str(e) for e in field_errors]
            
            return JsonResponse({
                "success": False,
                "error": "Error al completar datos de facturación",
                "form_errors": errors,
            }, status=400)
    
    # Validar que el cliente esté listo para facturar
    validacion = validar_cliente_para_facturacion(cliente)
    
    if not validacion["is_ready"]:
        # Retornar información para mostrar el modal
        return JsonResponse({
            "success": False,
            "needs_billing_data": True,
            "cliente": {
                "id": cliente.id,
                "nombre": str(cliente),
            },
            "missing_fields": validacion["missing_fields"],
            "message": validacion["message"],
        })
    
    # Generar CSV
    output = StringIO()
    writer = csv.writer(output)
    
    # Encabezados según formato SII (ajustar según requerimientos específicos)
    writer.writerow([
        "Fecha",
        "Tipo Documento",
        "Número Documento",
        "Cliente",
        "RUT/TAX_ID",
        "Giro",
        "Dirección",
        "Subtotal",
        "IVA",
        "Total",
    ])
    
    # Calcular totales del documento
    subtotal_repuestos = sum(
        linea.cantidad * linea.precio_unitario
        for linea in documento.lineas_repuesto.all()
    )
    subtotal_servicios = sum(
        linea.precio_unitario
        for linea in documento.lineas_servicio.all()
    )
    subtotal_otros = sum(
        linea.precio_cliente
        for linea in documento.lineas_otro_servicio.all()
    )
    subtotal = subtotal_repuestos + subtotal_servicios + subtotal_otros
    
    # Calcular IVA (ajustar según configuración de empresa)
    incluir_iva = getattr(documento, "incluir_iva", True)
    tasa_iva = 0.19  # TODO: Obtener de ConfiguracionEmpresa
    iva = subtotal * tasa_iva if incluir_iva else 0
    total = subtotal + iva
    
    # Obtener dirección
    direccion = ""
    if cliente.billing_address:
        direccion = cliente.billing_address.full_address
    elif cliente.ciudad:
        direccion = f"{cliente.direccion or ''}, {cliente.ciudad.nombre}".strip()
    elif cliente.ciudad_usa:
        direccion = f"{cliente.direccion or ''}, {cliente.ciudad_usa.nombre}".strip()
    else:
        direccion = cliente.direccion or ""
    
    # Fila de datos
    writer.writerow([
        documento.fecha.strftime("%d/%m/%Y") if documento.fecha else "",
        documento.tipo_documento or "",
        documento.numero_documento or "",
        str(cliente),
        cliente.tax_id or "",
        cliente.giro or "",
        direccion,
        f"{subtotal:.2f}",
        f"{iva:.2f}",
        f"{total:.2f}",
    ])
    
    # Crear respuesta HTTP con CSV
    response = HttpResponse(
        output.getvalue(),
        content_type="text/csv; charset=utf-8"
    )
    response["Content-Disposition"] = (
        f'attachment; filename="factura_sii_{documento.numero_documento}_{datetime.now().strftime("%Y%m%d")}.csv"'
    )
    
    return response


@login_required
@require_http_methods(["GET"])
def verificar_facturacion_documento(request, documento_id):
    """
    Verifica si el cliente del documento está listo para facturar.
    
    GET /documentos/<id>/verificar-facturacion/
    """
    empresa = getattr(request.user, "empresa", None)
    if not empresa:
        return JsonResponse({"success": False, "error": "No empresa found"}, status=400)
    
    documento = get_object_or_404(Documento, id=documento_id, empresa=empresa)
    
    if not documento.cliente:
        return JsonResponse({
            "success": False,
            "error": "El documento no tiene cliente asignado"
        }, status=400)
    
    cliente = documento.cliente
    validacion = validar_cliente_para_facturacion(cliente)
    profile_status = cliente.get_profile_status()
    
    return JsonResponse({
        "success": True,
        "is_ready": validacion["is_ready"],
        "cliente": {
            "id": cliente.id,
            "nombre": str(cliente),
        },
        "missing_fields": validacion["missing_fields"],
        "profile_status": profile_status,
        "message": validacion["message"],
    })
