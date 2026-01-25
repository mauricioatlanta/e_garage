"""
Vistas para seguimiento público y gestión de memoria/evidencias
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.translation import gettext_lazy as _

from taller.models.documento import Documento
from taller.models.memoria_seguimiento import (
    EvidenciaDocumento,
    NotaInterna,
    EtiquetaInterna,
    EtiquetaAsignacion,
    SeguimientoPublico,
)
from taller.auth.decorators_role import is_staff_member


def seguimiento_publico(request, token):
    """
    Vista pública para seguimiento de documentos (sin login).
    Muestra estado y evidencias compartibles, NO muestra notas/etiquetas internas.
    """
    try:
        seguimiento = SeguimientoPublico.objects.select_related(
            "documento", "documento__cliente", "documento__vehiculo", "empresa"
        ).get(token=token, activo=True)
    except SeguimientoPublico.DoesNotExist:
        raise Http404(_("Seguimiento no encontrado o inactivo"))

    documento = seguimiento.documento

    # Obtener evidencias compartibles
    evidencias = EvidenciaDocumento.objects.filter(documento=documento, compartible=True).order_by(
        "-created_at"
    )

    # Calcular totales
    from decimal import Decimal

    repuestos = list(documento.lineas_repuesto.all())
    servicios = list(documento.lineas_servicio.all())
    otros_servicios = list(documento.lineas_otro_servicio.all())

    subtotal_repuestos = sum(
        Decimal(str(linea.subtotal)) if hasattr(linea, "subtotal") else Decimal("0.00")
        for linea in repuestos
    )
    subtotal_servicios = sum(
        Decimal(str(linea.subtotal)) if hasattr(linea, "subtotal") else Decimal("0.00")
        for linea in servicios
    )
    subtotal_otros_servicios = sum(
        Decimal(str(otro.subtotal)) if hasattr(otro, "subtotal") else Decimal("0.00")
        for otro in otros_servicios
    )

    subtotal = subtotal_repuestos + subtotal_servicios + subtotal_otros_servicios
    iva = documento.tax_amount or Decimal("0.00")
    total = documento.total or Decimal("0.00")

    context = {
        "documento": documento,
        "seguimiento": seguimiento,
        "evidencias": evidencias,
        "lineas_repuesto": repuestos,
        "lineas_servicio": servicios,
        "lineas_otro_servicio": otros_servicios,
        "subtotal_repuestos": subtotal_repuestos,
        "subtotal_servicios": subtotal_servicios,
        "subtotal_otros_servicios": subtotal_otros_servicios,
        "subtotal": subtotal,
        "iva": iva,
        "total": total,
    }

    return render(request, "taller/common/documentos/seguimiento_publico.html", context)


@login_required
def gestionar_memoria_documento(request, documento_id):
    """
    Vista para gestionar memoria (notas y etiquetas) de un documento.
    Solo accesible para usuarios autenticados de la misma empresa.
    Multi-tenant: empresa forzada desde request.user.empresa
    """
    # Multi-tenant: forzar empresa del usuario
    empresa = request.user.empresa
    documento = get_object_or_404(Documento.objects.filter(empresa=empresa), id=documento_id)

    # Verificar permisos
    es_staff = is_staff_member(request.user)

    # Multi-tenant: todas las queries filtran por empresa
    # Obtener notas (filtrar por solo_staff si es técnico)
    if es_staff:
        notas = NotaInterna.objects.filter(documento=documento, empresa=empresa).order_by(
            "-created_at"
        )
    else:
        notas = NotaInterna.objects.filter(
            documento=documento, empresa=empresa, solo_staff=False
        ).order_by("-created_at")

    # Obtener etiquetas asignadas (filtrar por solo_staff si es técnico)
    if es_staff:
        etiquetas_asignadas = EtiquetaAsignacion.objects.filter(
            documento=documento, empresa=empresa
        ).select_related("etiqueta")
    else:
        etiquetas_asignadas = EtiquetaAsignacion.objects.filter(
            documento=documento, empresa=empresa, etiqueta__solo_staff=False
        ).select_related("etiqueta")

    # Obtener todas las etiquetas disponibles (filtrar por solo_staff si es técnico)
    if es_staff:
        etiquetas_disponibles = EtiquetaInterna.objects.filter(empresa=empresa)
    else:
        etiquetas_disponibles = EtiquetaInterna.objects.filter(empresa=empresa, solo_staff=False)

    # Obtener evidencias (multi-tenant: filtrar por empresa)
    evidencias = EvidenciaDocumento.objects.filter(documento=documento, empresa=empresa).order_by(
        "-created_at"
    )
    fotos_count = evidencias.filter(tipo="FOTO").count()
    videos_count = evidencias.filter(tipo="VIDEO").count()

    # Obtener seguimiento público si existe
    seguimiento_publico = getattr(documento, "seguimiento_publico", None)

    context = {
        "documento": documento,
        "notas": notas,
        "etiquetas_asignadas": etiquetas_asignadas,
        "etiquetas_disponibles": etiquetas_disponibles,
        "evidencias": evidencias,
        "fotos_count": fotos_count,
        "videos_count": videos_count,
        "puede_agregar_foto": fotos_count < 4,
        "puede_agregar_video": videos_count < 1,
        "seguimiento_publico": seguimiento_publico,
        "es_staff": es_staff,
    }

    return render(request, "documentos/gestionar_memoria.html", context)


@login_required
@require_http_methods(["POST"])
def crear_seguimiento_publico(request, documento_id):
    """
    Crea o activa un seguimiento público para un documento.
    Multi-tenant: empresa forzada desde request.user.empresa
    """
    # Multi-tenant: forzar empresa del usuario
    empresa = request.user.empresa
    documento = get_object_or_404(Documento.objects.filter(empresa=empresa), id=documento_id)

    # Multi-tenant: empresa forzada (nunca confiar en POST)
    seguimiento, created = SeguimientoPublico.objects.get_or_create(
        documento=documento,
        defaults={"empresa": empresa, "activo": True},
    )

    if not created:
        seguimiento.activo = True
        seguimiento.empresa = empresa  # Forzar empresa en updates
        seguimiento.save()

    messages.success(request, _("Seguimiento público creado exitosamente"))
    return redirect("documentos:gestionar_memoria", documento_id=documento_id)
