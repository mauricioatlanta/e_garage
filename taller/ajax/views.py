"""AJAX endpoints compartidos para búsquedas rápidas en formularios.

Estos helpers devuelven exactamente el JSON que esperan los scripts del
formulario de documentos: un objeto con la clave ``results`` y elementos que
incluyen los campos `id`, `text`, y metadatos adicionales.
"""

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from taller.models.clientes import Cliente
from taller.models.vehiculos import Vehiculo


def _empresa_desde_request(request):
    if not request.user.is_authenticated:
        return None
    return getattr(request.user, "empresa", None)


def _label_cliente(cliente: Cliente) -> str:
    partes = []
    nombre = getattr(cliente, "nombre", "")
    apellido = getattr(cliente, "apellido", "")
    if nombre:
        partes.append(nombre)
    if apellido:
        partes.append(apellido)
    etiqueta = " ".join(partes).strip()

    if not etiqueta:
        etiqueta = (
            getattr(cliente, "nombre_completo", None)
            or getattr(cliente, "razon_social", None)
            or getattr(cliente, "nombre_fantasia", None)
            or f"Cliente #{cliente.pk}"
        )
    return etiqueta


def _label_vehiculo(vehiculo: Vehiculo) -> str:
    if hasattr(vehiculo, "display_label"):
        etiqueta = vehiculo.display_label()
        if etiqueta:
            return etiqueta

    marca = getattr(getattr(vehiculo, "marca", None), "nombre", "") or getattr(
        vehiculo, "marca", ""
    )
    modelo = getattr(getattr(vehiculo, "modelo", None), "nombre", "") or getattr(
        vehiculo, "modelo", ""
    )
    anio = getattr(vehiculo, "anio", "") or getattr(vehiculo, "year", "")
    placa = getattr(vehiculo, "patente", "") or getattr(vehiculo, "placa", "")
    vin = getattr(vehiculo, "vin", "")

    partes = [str(anio) if anio else "", marca, modelo]
    partes = [p for p in partes if p]

    cola = placa or (vin[-6:] if vin else "")
    base = " ".join(partes).strip()
    if base and cola:
        return f"{base} • {cola}"
    return base or cola or f"Vehículo #{vehiculo.pk}"


def _respuesta_vacia(status=200):
    return JsonResponse({"results": []}, status=status)


@login_required
@require_GET
def buscar_clientes(request):
    termino = (request.GET.get("q") or "").strip()
    if len(termino) < 2:
        return _respuesta_vacia()

    empresa = _empresa_desde_request(request)
    if not empresa:
        return _respuesta_vacia()

    qs = Cliente.objects.filter(empresa=empresa)
    campos = {f.name for f in Cliente._meta.get_fields()}
    filtros = Q()
    for campo in (
        "nombre",
        "apellido",
        "nombre_completo",
        "razon_social",
        "nombre_fantasia",
        "email",
        "telefono",
        "tax_id",
        "documento",
    ):
        if campo in campos:
            filtros |= Q(**{f"{campo}__icontains": termino})
    if filtros:
        qs = qs.filter(filtros)
    qs = qs.order_by("nombre")[:15]

    results = [
        {
            "id": cliente.id,
            "text": _label_cliente(cliente),
            "email": getattr(cliente, "email", "") or "",
            "telefono": getattr(cliente, "telefono", "") or getattr(cliente, "fono", "") or "",
        }
        for cliente in qs
    ]
    return JsonResponse({"results": results})


@login_required
@require_GET
def vehiculos_por_cliente(request):
    cliente_id = request.GET.get("cliente_id") or request.GET.get("cliente")
    if not cliente_id:
        return _respuesta_vacia()

    try:
        cliente_id_int = int(cliente_id)
    except (TypeError, ValueError):
        return _respuesta_vacia()

    empresa = _empresa_desde_request(request)
    if not empresa:
        return _respuesta_vacia()

    qs = (
        Vehiculo.objects.filter(empresa=empresa, cliente_id=cliente_id_int)
        .select_related("marca", "modelo")
        .order_by("-id")[:50]
    )

    results = [
        {
            "id": vehiculo.id,
            "text": _label_vehiculo(vehiculo),
        }
        for vehiculo in qs
    ]
    return JsonResponse({"results": results})
