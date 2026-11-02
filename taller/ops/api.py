"""
APIs JSON para Centro de Ingreso Pro: OCR, búsqueda vehículo/repuesto, checklist, add repuesto.
"""

import json
import tempfile
from decimal import Decimal

from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

from taller.auth.decorators import login_required_default
from taller.models import (
    ChecklistIngreso,
    Documento,
    LineaRepuesto,
    Repuesto,
    Vehiculo,
)


def _empresa(request):
    return getattr(request.user, "empresa", None) if request.user.is_authenticated else None


@login_required_default
@require_POST
def api_ocr_patente(request):
    """Recibe imagen; retorna candidatos de patente. Si OCR no disponible, success: false."""
    from taller.utils.ocr import is_ocr_available, ocr_read_text, extraer_candidatos_patente

    if not is_ocr_available():
        return JsonResponse({"success": False, "error": "OCR no disponible"})
    f = request.FILES.get("image")
    if not f:
        return JsonResponse({"success": False, "error": "Falta imagen"})
    try:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            for chunk in f.chunks():
                tmp.write(chunk)
            tmp.flush()
            raw = ocr_read_text(tmp.name)
        import os

        try:
            os.unlink(tmp.name)
        except Exception:
            pass
        candidates = extraer_candidatos_patente(raw, top=5)
        return JsonResponse({"success": True, "candidates": candidates})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


@login_required_default
@require_POST
def api_ocr_repuesto(request):
    """Recibe imagen; retorna candidatos de código repuesto."""
    from taller.utils.ocr import is_ocr_available, ocr_read_text, extraer_candidatos_repuesto

    if not is_ocr_available():
        return JsonResponse({"success": False, "error": "OCR no disponible"})
    f = request.FILES.get("image")
    if not f:
        return JsonResponse({"success": False, "error": "Falta imagen"})
    try:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            for chunk in f.chunks():
                tmp.write(chunk)
            tmp.flush()
            raw = ocr_read_text(tmp.name)
        import os

        try:
            os.unlink(tmp.name)
        except Exception:
            pass
        candidates = extraer_candidatos_repuesto(raw, top=10)
        return JsonResponse({"success": True, "candidates": candidates})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


@login_required_default
@require_GET
def api_buscar_vehiculo(request):
    """GET ?patente= → existe, vehiculo id, marca/modelo, cliente."""
    empresa = _empresa(request)
    if not empresa:
        return JsonResponse({"success": False, "error": "Sin empresa"})
    patente = (request.GET.get("patente") or "").strip().upper().replace(" ", "").replace("-", "")
    if not patente:
        return JsonResponse({"success": False, "error": "Falta patente"})
    vehiculo = (
        Vehiculo.objects.filter(empresa=empresa, patente=patente).select_related("cliente").first()
    )
    if not vehiculo:
        return JsonResponse({"success": True, "existe": False})
    return JsonResponse(
        {
            "success": True,
            "existe": True,
            "vehiculo_id": vehiculo.pk,
            "marca": vehiculo.get_marca_display(),
            "modelo": vehiculo.get_modelo_display(),
            "cliente_id": vehiculo.cliente_id,
            "cliente_nombre": str(vehiculo.cliente),
        }
    )


@login_required_default
@require_GET
def api_buscar_repuesto(request):
    """GET ?q= → top 10 repuestos por código o nombre."""
    empresa = _empresa(request)
    if not empresa:
        return JsonResponse({"success": False, "error": "Sin empresa"})
    q = (request.GET.get("q") or "").strip()
    if not q:
        return JsonResponse({"success": True, "items": []})
    from django.db.models import Q

    qs = Repuesto.objects.filter(empresa=empresa).filter(
        Q(part_number__icontains=q) | Q(nombre__icontains=q)
    )[:10]
    items = [
        {
            "id": r.pk,
            "codigo": r.part_number or "",
            "nombre": r.nombre,
            "precio_venta": str(r.precio_venta),
        }
        for r in qs
    ]
    return JsonResponse({"success": True, "items": items})


@login_required_default
@require_POST
def api_add_repuesto(request, documento_id):
    """POST: repuesto_id o codigo+nombre, cantidad, precio. Crea LineaRepuesto."""
    empresa = _empresa(request)
    if not empresa:
        return JsonResponse({"success": False, "error": "Sin empresa"})
    documento = Documento.objects.filter(pk=documento_id, empresa=empresa).first()
    if not documento:
        return JsonResponse({"success": False, "error": "Documento no encontrado"})
    repuesto_id = request.POST.get("repuesto_id")
    codigo = (request.POST.get("codigo") or "").strip()
    nombre = (request.POST.get("nombre") or "").strip()
    try:
        cantidad = int(request.POST.get("cantidad", 1))
    except (ValueError, TypeError):
        cantidad = 1
    try:
        precio = Decimal(request.POST.get("precio_unitario", "0"))
    except Exception:
        precio = Decimal("0")
    if repuesto_id:
        rep = Repuesto.objects.filter(pk=repuesto_id, empresa=empresa).first()
        if rep:
            codigo = rep.part_number or codigo or str(rep.pk)
            nombre = rep.nombre
            if precio <= 0:
                precio = rep.precio_venta
    if not nombre:
        nombre = codigo or "Repuesto"
    if not codigo:
        codigo = f"LIBRE-{documento.lineas_repuesto.count() + 1}"
    LineaRepuesto.objects.create(
        documento=documento,
        repuesto_id=repuesto_id if repuesto_id else None,
        codigo=codigo,
        nombre=nombre,
        cantidad=cantidad,
        precio_unitario=precio,
    )
    documento.recompute_totals(persist=True)
    return JsonResponse({"success": True, "message": "Línea agregada"})


@login_required_default
@require_POST
def api_checklist_save(request, documento_id):
    """POST JSON: danos, nivel_combustible, objetos_valor, luces_funcionan."""
    empresa = _empresa(request)
    if not empresa:
        return JsonResponse({"success": False, "error": "Sin empresa"})
    documento = Documento.objects.filter(pk=documento_id, empresa=empresa).first()
    if not documento:
        return JsonResponse({"success": False, "error": "Documento no encontrado"})
    try:
        body = json.loads(request.body) if request.body else {}
    except Exception:
        body = request.POST.dict()
    danos = body.get("danos", {})
    nivel_combustible = body.get("nivel_combustible", 0)
    objetos_valor = body.get("objetos_valor", "")
    luces_funcionan = body.get("luces_funcionan", True)
    checklist, _ = ChecklistIngreso.objects.get_or_create(
        documento=documento,
        defaults={"nivel_combustible": 0, "luces_funcionan": True, "objetos_valor": ""},
    )
    checklist.danos = danos if isinstance(danos, dict) else {}
    checklist.nivel_combustible = int(nivel_combustible) if nivel_combustible is not None else 0
    checklist.objetos_valor = objetos_valor or ""
    checklist.luces_funcionan = bool(luces_funcionan)
    checklist.save()
    return JsonResponse({"success": True})
