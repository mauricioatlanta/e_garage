import datetime
import zoneinfo

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET

from taller.models import Cliente
from taller.models.documento import Documento
from taller.models.vehiculos import Vehiculo
from taller.utils.empresa import get_active_empresa, get_or_create_empresa, get_user_empresa_safe


def _workspace_prefix_from_request(request):
    path = (request.path or "").strip("/").split("/")
    valid_countries = {"ar", "br", "cl", "co", "ec", "mx", "pe", "us", "uy", "ve"}

    country = path[0].lower() if path else ""
    lang = path[1].lower() if len(path) > 1 and len(path[1]) == 2 else None

    if country not in valid_countries:
        empresa = get_user_empresa_safe(getattr(request, "user", None))
        country = (getattr(empresa, "pais", "") or getattr(request, "country", "") or "cl").lower()
        if country not in valid_countries:
            country = "cl"

    if country == "us":
        lang = lang or ("en" if getattr(request, "LANGUAGE_CODE", "en") == "en" else "es")
    else:
        lang = lang or "es"

    return f"/{country}/{lang}"


def _full_name(nombre, apellido):
    return " ".join(part for part in [nombre, apellido] if part).strip()


def ingreso_centro(request, *args, **kwargs):
    from taller.views.workspace_dashboard import workspace_dashboard
    return workspace_dashboard(request, *args, **kwargs)


@require_GET
@login_required
def ingreso_buscar(request, *args, **kwargs):
    q = (request.GET.get("q") or "").strip()
    workspace_prefix = _workspace_prefix_from_request(request)

    if len(q) < 2:
        return JsonResponse(
            {
                "query": q,
                "vehiculos": [],
                "clientes": [],
                "meta": {
                    "min_chars": 2,
                    "vehiculos": 0,
                    "clientes": 0,
                    "total": 0,
                },
            }
        )

    empresa = get_active_empresa(request) or get_user_empresa_safe(request.user)
    if not empresa:
        empresa = get_or_create_empresa(request)
    if not empresa:
        return JsonResponse(
            {
                "query": q,
                "vehiculos": [],
                "clientes": [],
                "meta": {
                    "min_chars": 2,
                    "vehiculos": 0,
                    "clientes": 0,
                    "total": 0,
                },
            }
        )

    vehiculos = (
        Vehiculo.objects.select_related("cliente", "marca", "modelo")
        .filter(
            empresa=empresa,
            tipo_uso=Vehiculo.TIPO_USO_CLIENTE,
        )
        .filter(
            Q(patente__istartswith=q)
            | Q(vin__icontains=q)
            | Q(cliente__nombre__icontains=q)
            | Q(cliente__apellido__icontains=q)
            | Q(cliente__telefono__icontains=q)
            | Q(cliente__email__icontains=q)
            | Q(cliente__tax_id__istartswith=q)
        )
        .order_by("patente", "id")[:6]
    )

    clientes = (
        Cliente.objects.filter(empresa=empresa)
        .filter(
            Q(nombre__icontains=q)
            | Q(apellido__icontains=q)
            | Q(telefono__icontains=q)
            | Q(email__icontains=q)
            | Q(tax_id__istartswith=q)
        )
        .order_by("nombre", "apellido", "id")[:6]
    )

    vehiculos_data = []
    for vehiculo in vehiculos:
        cliente_nombre = (
            _full_name(vehiculo.cliente.nombre, vehiculo.cliente.apellido)
            if vehiculo.cliente
            else ""
        )
        marca_modelo = " ".join(
            part
            for part in [vehiculo.get_marca_display(), vehiculo.get_modelo_display()]
            if part and not part.startswith("Sin ")
        ).strip()

        vehiculos_data.append(
            {
                "id": vehiculo.id,
                "type": "vehiculo",
                "title": vehiculo.patente or vehiculo.vin or f"Vehiculo #{vehiculo.id}",
                "patente": vehiculo.patente or "",
                "vin": vehiculo.vin or "",
                "cliente": cliente_nombre,
                "subtitle": marca_modelo,
                "year": vehiculo.anio,
                "meta": cliente_nombre or "Sin cliente asignado",
                "url": f"{workspace_prefix}/vehiculos/{vehiculo.id}/panel-ingreso/",
            }
        )

    clientes_data = []
    for cliente in clientes:
        nombre_completo = _full_name(cliente.nombre, cliente.apellido)
        clientes_data.append(
            {
                "id": cliente.id,
                "type": "cliente",
                "title": nombre_completo or cliente.email or f"Cliente #{cliente.id}",
                "nombre": nombre_completo,
                "telefono": cliente.telefono or "",
                "email": cliente.email or "",
                "tax_id": cliente.tax_id or "",
                "subtitle": cliente.telefono or cliente.email or "Sin contacto principal",
                "meta": cliente.tax_id or cliente.email or "",
                "url": f"{workspace_prefix}/clientes/ver/{cliente.id}/",
            }
        )

    return JsonResponse(
        {
            "query": q,
            "vehiculos": vehiculos_data,
            "clientes": clientes_data,
            "meta": {
                "min_chars": 2,
                "vehiculos": len(vehiculos_data),
                "clientes": len(clientes_data),
                "total": len(vehiculos_data) + len(clientes_data),
            },
        }
    )


@login_required
def panel_ingreso_vehiculo(request, pk, *args, **kwargs):
    empresa = get_active_empresa(request) or get_user_empresa_safe(request.user)
    vehiculo_filters = {"pk": pk}
    if empresa:
        vehiculo_filters["empresa"] = empresa
    vehiculo = get_object_or_404(Vehiculo, **vehiculo_filters)

    posibles_rutas = [
        "vehiculos:ver_vehiculo",
        "vehiculos:detalle",
        "vehiculos:vehiculo_detalle",
        "taller:vehiculo_detalle",
        "vehiculo_detalle",
    ]

    for ruta in posibles_rutas:
        try:
            return redirect(ruta, vehiculo_id=vehiculo.pk)
        except Exception:
            continue

    return redirect(f"{_workspace_prefix_from_request(request)}/vehiculos/{vehiculo.pk}/")


@require_GET
@login_required
def workspace_live_feed(request, *args, **kwargs):
    empresa = get_active_empresa(request) or get_user_empresa_safe(request.user)
    if not empresa:
        return JsonResponse(
            {"en_taller": [], "entregados_hoy": [], "kpis": {"en_taller": 0, "entregados_hoy": 0}}
        )

    tz = zoneinfo.ZoneInfo(empresa.zona_horaria or "UTC")
    hoy_local = datetime.datetime.now(tz=tz).date()
    workspace_prefix = _workspace_prefix_from_request(request)

    en_taller_qs = (
        Documento.objects.filter(empresa=empresa, estado="BORRADOR")
        .select_related(
            "vehiculo", "vehiculo__marca", "vehiculo__modelo", "cliente", "tecnico_responsable"
        )
        .order_by("fecha_emision")[:30]
    )

    entregados_hoy_qs = (
        Documento.objects.filter(empresa=empresa, estado="EMITIDO", fecha_emision=hoy_local)
        .select_related(
            "vehiculo", "vehiculo__marca", "vehiculo__modelo", "cliente", "tecnico_responsable"
        )
        .order_by("-fecha_emision")[:15]
    )

    def _serialize(doc):
        v = doc.vehiculo
        c = doc.cliente
        t = doc.tecnico_responsable
        marca_modelo = ""
        if v:
            partes = [v.get_marca_display() or "", v.get_modelo_display() or ""]
            marca_modelo = " ".join(p for p in partes if p).strip()
        url = f"{workspace_prefix}/documentos/ver/{doc.pk}/"
        return {
            "id": doc.id,
            "patente": (v.patente if v else "") or "",
            "vehiculo": marca_modelo,
            "cliente": _full_name(c.nombre, c.apellido) if c else "",
            "tecnico": t.nombre if t else "",
            "creado_en": doc.created_at.astimezone(tz).isoformat(),
            "url": url,
        }

    en_taller = [_serialize(d) for d in en_taller_qs]
    entregados_hoy = [_serialize(d) for d in entregados_hoy_qs]

    return JsonResponse(
        {
            "en_taller": en_taller,
            "entregados_hoy": entregados_hoy,
            "kpis": {"en_taller": len(en_taller), "entregados_hoy": len(entregados_hoy)},
        }
    )


@login_required
def centro_de_mando(request, *args, **kwargs):
    empresa = get_active_empresa(request) or get_user_empresa_safe(request.user)
    return render(request, "taller/workspace/centro_de_mando.html", {"empresa": empresa})
