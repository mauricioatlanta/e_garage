from django.apps import apps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import FieldError
from django.db import models
from django.http import JsonResponse


def _get_empresa(request):
    # varios fallbacks comunes en eGarage
    empresa = getattr(request, "empresa", None)
    if empresa:
        return empresa
    user = getattr(request, "user", None)
    if not user:
        return None
    empresa = getattr(user, "empresa", None)
    if empresa:
        return empresa
    perfil = getattr(user, "perfil", None) or getattr(user, "profile", None)
    if perfil:
        return getattr(perfil, "empresa", None)
    return None


def _existing_fields(Model):
    return {f.name for f in Model._meta.get_fields()}


def _q_for_fields(Model, q, candidates):
    fields = _existing_fields(Model)
    qq = models.Q()
    used = 0
    for f in candidates:
        if f in fields:
            qq |= models.Q(**{f"{f}__icontains": q})
            used += 1
    return qq if used else None


@login_required
def autocomplete_servicio(request):
    q = request.GET.get("q", "").strip()
    empresa = _get_empresa(request)
    if not empresa:
        return JsonResponse([], safe=False)

    Servicio = apps.get_model("taller", "Servicio")
    qs = Servicio.objects.all()

    # filtra por empresa si existe campo
    try:
        qs = qs.filter(empresa=empresa)
    except Exception:
        pass

    if q:
        try:
            qs = qs.filter(
                models.Q(nombre__icontains=q)
                | models.Q(categoria__nombre__icontains=q)
                | models.Q(categoria__code__icontains=q)
            )
        except (FieldError, Exception):
            # fallback mínimo
            try:
                qs = qs.filter(nombre__icontains=q)
            except Exception:
                pass

    qs = qs.order_by("nombre")[:20]

    data = []
    for s in qs:
        data.append({
            "id": s.pk,
            "nombre": getattr(s, "nombre", str(s)),
            "descripcion": getattr(s, "nombre", str(s)),
            "precio": 0,  # en eGarage el precio del servicio se define en el documento
        })
    return JsonResponse(data, safe=False)


@login_required
def autocomplete_repuesto(request):
    q = request.GET.get("q", "").strip()
    empresa = _get_empresa(request)
    if not empresa:
        return JsonResponse([], safe=False)

    Repuesto = apps.get_model("taller", "Repuesto")
    qs = Repuesto.objects.all()

    # filtra por empresa si existe campo
    for field in ("empresa", "company"):
        try:
            qs = qs.filter(**{field: empresa})
            break
        except Exception:
            continue

    if q:
        qq = _q_for_fields(Repuesto, q, ["nombre", "codigo", "part_number", "numero_parte", "sku"])
        if qq is not None:
            qs = qs.filter(qq)

    qs = qs.order_by("nombre")[:20]

    data = []
    for r in qs:
        nombre = getattr(r, "nombre", str(r))
        codigo = (
            getattr(r, "part_number", None)
            or getattr(r, "numero_parte", None)
            or getattr(r, "codigo", None)
            or ""
        )
        data.append({
            "id": r.pk,
            "nombre": nombre,
            "codigo": codigo,
            "descripcion": f"{codigo} - {nombre}".strip(" -"),
        })
    return JsonResponse(data, safe=False)


@login_required
def autocomplete_cliente(request):
    q = request.GET.get("q", "").strip()
    empresa = _get_empresa(request)
    if not empresa:
        return JsonResponse({"results": []})

    Cliente = apps.get_model("taller", "Cliente")
    qs = Cliente.objects.all()

    for field in ("empresa", "company"):
        try:
            qs = qs.filter(**{field: empresa})
            break
        except Exception:
            continue

    if q:
        qq = _q_for_fields(Cliente, q, ["nombre", "rut", "ein", "telefono", "email"])
        if qq is not None:
            qs = qs.filter(qq)

    qs = qs.order_by("nombre")[:20]

    results = []
    for c in qs:
        results.append({
            "id": c.pk,
            "text": getattr(c, "nombre", str(c)),
            "rut": getattr(c, "rut", "") or getattr(c, "ein", ""),
            "email": getattr(c, "email", ""),
            "telefono": getattr(c, "telefono", ""),
        })

    return JsonResponse({"results": results})


@login_required
def autocomplete_otro_servicio(request):
    q = request.GET.get("q", "").strip()
    empresa = _get_empresa(request)
    if not empresa:
        return JsonResponse([], safe=False)

    try:
        LineaOtroServicio = apps.get_model("taller", "LineaOtroServicio")
    except LookupError:
        return JsonResponse([], safe=False)

    qs = LineaOtroServicio.objects.all()

    # intenta filtrar por empresa vía documento
    try:
        qs = qs.filter(documento__empresa=empresa)
    except Exception:
        pass

    if q:
        qq = _q_for_fields(LineaOtroServicio, q, ["nombre", "empresa_externa"])
        if qq is not None:
            qs = qs.filter(qq)

    qs = qs.order_by("-id")[:20]

    data = []
    for x in qs:
        data.append({
            "id": x.pk,
            "nombre": getattr(x, "nombre", str(x)),
            "empresa_externa": getattr(x, "empresa_externa", ""),
        })
    return JsonResponse(data, safe=False)






