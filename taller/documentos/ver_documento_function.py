from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from .models import Documento


@login_required
def ver_documento(request, documento_id):
    """
    Vista para mostrar un documento con validación multi-tenant y cálculos precisos.
    
    Características:
    - 🔒 Seguro: filtra por empresa=request.user.empresa
    - 📐 Preciso: usa Decimal, evita floats
    - ⚖️ Consistente: usa campos calculados del modelo (signals)
    - 🛠 Flexible: separa líneas por tipo (repuesto, servicio)
    """
    # Forzar multi-tenant: el documento debe pertenecer a la empresa del usuario
    documento = get_object_or_404(
        Documento.objects.select_related("empresa"),
        id=documento_id,
        empresa=request.user.empresa,
    )

    # Usa los campos ya calculados en el modelo (mantiene consistencia con signals)
    subtotal_repuestos = getattr(documento, "neto_repuestos", Decimal("0.00"))
    subtotal_servicios = getattr(documento, "neto_servicios", Decimal("0.00"))
    subtotal = subtotal_repuestos + subtotal_servicios
    iva = getattr(documento, "tax_amount", Decimal("0.00"))
    total = getattr(documento, "total", subtotal + iva)

    # Cargar líneas relacionadas usando related_names correctos
    # Los modelos tienen related_names específicos:
    # - LineaRepuesto: related_name="lineas_repuesto"
    # - LineaServicio: related_name="lineas_servicio"  
    # - LineaOtroServicio: related_name="lineas_otro_servicio"
    lineas_repuesto = documento.lineas_repuesto.all()
    lineas_servicio = documento.lineas_servicio.all()
    lineas_otro_servicio = documento.lineas_otro_servicio.all()
    
    # Para compatibilidad con templates existentes, combinar todas las líneas
    detalles = list(lineas_repuesto) + list(lineas_servicio) + list(lineas_otro_servicio)

    return render(
        request,
        "taller/documentos/ver_documento.html",
        {
            "documento": documento,
            "detalles": detalles,  # Para compatibilidad
            "lineas_repuesto": lineas_repuesto,
            "lineas_servicio": lineas_servicio,
            "lineas_otro_servicio": lineas_otro_servicio,
            "subtotal_repuestos": subtotal_repuestos,
            "subtotal_servicios": subtotal_servicios,
            "subtotal": subtotal,
            "iva": iva,
            "total": total,
        },
    )
