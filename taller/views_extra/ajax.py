from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse

from taller.models.clientes import Cliente
from taller.models.vehiculos import Vehiculo
from taller.utils.empresa import get_or_create_empresa
from utils import pais


def _safe_fields(model):
    return {f.name for f in model._meta.get_fields()}


@login_required
def buscar_clientes(request):
    empresa = get_or_create_empresa(request)
    q = (request.GET.get("q") or "").strip()
    page = int(request.GET.get("page") or 1)

    qs = Cliente.objects.filter(empresa=empresa)

    if q:
        fields = _safe_fields(Cliente)
        terms = q.split()
        for t in terms:
            cond = Q(nombre__icontains=t)
            if "apellido" in fields:
                cond |= Q(apellido__icontains=t)
            if "tax_id" in fields:
                cond |= Q(tax_id__icontains=t)
            if "telefono" in fields:
                cond |= Q(telefono__icontains=t)
            if "email" in fields:
                cond |= Q(email__icontains=t)
            qs = qs.filter(cond)

    qs = qs.order_by("nombre")
    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(page)

    results = []
    fields = _safe_fields(Cliente)
    for c in page_obj.object_list:
        # 🚀 BISTURÍ: Construir texto con nombre+apellido
        nombre_parts = [c.nombre]
        if "apellido" in fields and getattr(c, "apellido", None):
            nombre_parts.append(getattr(c, "apellido"))
        text = " ".join(filter(None, nombre_parts))

        # Construir subtitle con info adicional
        extra = []
        if "tax_id" in fields and getattr(c, "tax_id", None):
            extra.append(getattr(c, "tax_id"))
        if "telefono" in fields and getattr(c, "telefono", None):
            extra.append(getattr(c, "telefono"))
        if "email" in fields and getattr(c, "email", None):
            extra.append(getattr(c, "email"))
        subtitle = " · ".join(extra) if extra else ""

        results.append(
            {
                "id": c.id,
                "text": text,
                "subtitle": subtitle,
            }
        )

    return JsonResponse(
        {
            "results": results,
            "more": page_obj.has_next(),
        }
    )


@login_required
def vehiculos_por_cliente(request):
    empresa = get_or_create_empresa(request)
    # 🚀 BISTURÍ: Aceptar tanto 'cliente' como 'cliente_id'
    cliente_id = request.GET.get("cliente") or request.GET.get("cliente_id")
    if not cliente_id:
        return JsonResponse({"results": []})

    qs = (
        Vehiculo.objects.filter(empresa=empresa, cliente_id=cliente_id)
        .select_related("marca", "modelo")
        .order_by("-id")[:50]
    )

    def _name(v):
        marca = (
            v.get_marca_display()
            if hasattr(v, "get_marca_display")
            else (
                getattr(getattr(v, "marca", None), "nombre", "")
                or getattr(v, "marca_texto", "")
                or ""
            )
        )
        modelo = (
            v.get_modelo_display()
            if hasattr(v, "get_modelo_display")
            else (
                getattr(getattr(v, "modelo", None), "nombre", "")
                or getattr(v, "modelo_texto", "")
                or ""
            )
        )
        tag = getattr(v, "patente", None) or getattr(v, "vin", None) or ""
        parts = [p for p in [marca, modelo, tag] if p]
        return " ".join(parts) if parts else f"Vehículo #{v.pk}"

    return JsonResponse({"results": [{"id": v.pk, "text": _name(v)} for v in qs]})


def ciudades_por_region(request):
    pais_codigo = request.GET.get("pais")
    region = request.GET.get("region")
    ciudades = pais.get_ciudades(pais_codigo, region)
    return JsonResponse({"ciudades": ciudades})
