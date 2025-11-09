"""eGarage — módulo limpiado para pre-commit (docstring al inicio)."""

# """
# Helpers para APIs y vistas AJAX - Multi-Tenant Safe

# Provee:
#   - Respuestas JSON estandarizadas
#   - Scoping automático por empresa/país
#   - Decoradores de seguridad
#   - Utilidades de validación
# """

from functools import wraps

from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

# =========================
# Respuestas Estandarizadas
# =========================


def ok(**payload):
    """
    Respuesta exitosa estandarizada.

    Uso:
        return ok(modelos=[{"id": "1", "nombre": "Corolla"}])
        # → {"success": true, "modelos": [...]}
    """
    return JsonResponse({"success": True, **payload})


def bad(msg, status=400):
    """
    Respuesta de error estandarizada.

    Uso:
        return bad("Falta parámetro 'marca_id'", status=400)
        # → {"success": false, "error": "..."}, 400
    """
    return JsonResponse({"success": False, "error": msg}, status=status)


def dal_response(items, id_field="id", text_field="nombre"):
    """
    Respuesta compatible con Django Autocomplete Light.

    Uso:
        return dal_response(modelos, id_field="pk", text_field="nombre")
        # → {"results": [{"id": "1", "text": "Corolla"}]}
    """
    results = [
        {
            "id": str(getattr(item, id_field)),
            "text": str(getattr(item, text_field, item)),
        }
        for item in items
    ]
    return JsonResponse({"results": results})


# =========================
# Scoping Multi-Tenant
# =========================


def get_user_scope(request):
    """
    Obtiene empresa y país del usuario autenticado.

    Returns:
        tuple: (empresa, pais) donde pais es "CL" o "US"

    Uso:
        empresa, pais = get_user_scope(request)
        qs = Marca.objects.filter(country=pais)
        if hasattr(Marca, "empresa") and empresa:
            qs = qs.filter(empresa=empresa)
    """
    empresa = getattr(request.user, "empresa", None)
    raw_pais = (
        getattr(empresa, "pais", None) or getattr(request, "country", None) or "CL"
    )
    pais = str(raw_pais).strip().upper()
    pais = pais if pais in ("CL", "US") else "CL"
    return empresa, pais


def parse_int(value, name="id", default=None):
    """
    Convierte valor a int con manejo de errores.

    Args:
        value: Valor a convertir
        name: Nombre del parámetro (para mensajes de error)
        default: Valor por defecto si falla

    Returns:
        int o default

    Raises:
        ValueError: Si default es None y la conversión falla

    Uso:
        modelo_id = parse_int(request.GET.get("modelo_id"), "modelo_id")
    """
    try:
        return int(value)
    except (TypeError, ValueError):
        if default is not None:
            return default
        raise ValueError(f"Parámetro '{name}' debe ser un entero válido")


# =========================
# Decoradores de Seguridad
# =========================


def can_manage_catalog(user):
    """
    Verifica si el usuario puede gestionar catálogos (marca/modelo/motor/caja).

    Ajusta según tus permisos:
      - is_staff: administradores del sistema
      - has_perm("taller.add_modelo"): permisos específicos
      - user.empresa.tipo == "premium": planes de suscripción

    Uso como decorador:
        @user_passes_test(can_manage_catalog)
        def ajax_agregar_marca(request):
            ...
    """
    return user.is_staff or user.has_perm("taller.add_modelo")


def ajax_get(view_func):
    """
    Decorador combinado para endpoints AJAX GET.
    Aplica: @login_required + @require_http_methods(["GET"])

    Uso:
        @ajax_get
        def ajax_modelos_por_marca(request):
            ...
    """

    @wraps(view_func)
    @login_required
    @require_http_methods(["GET"])
    def wrapper(request, *args, **kwargs):
        return view_func(request, *args, **kwargs)

    return wrapper


def ajax_post(view_func):
    """
    Decorador combinado para endpoints AJAX POST.
    Aplica: @login_required + @require_http_methods(["POST"])

    Nota: CSRF se valida automáticamente con SessionAuthentication.

    Uso:
        @ajax_post
        def ajax_agregar_marca(request):
            ...
    """

    @wraps(view_func)
    @login_required
    @require_http_methods(["POST"])
    def wrapper(request, *args, **kwargs):
        return view_func(request, *args, **kwargs)

    return wrapper


def ajax_post_staff(view_func):
    """
    Decorador combinado para endpoints AJAX POST que requieren staff.
    Aplica: @login_required + @require_http_methods(["POST"]) + staff check

    Uso:
        @ajax_post_staff
        def ajax_agregar_marca(request):
            ...
    """

    @wraps(view_func)
    @login_required
    @require_http_methods(["POST"])
    @user_passes_test(can_manage_catalog)
    def wrapper(request, *args, **kwargs):
        return view_func(request, *args, **kwargs)

    return wrapper


# =========================
# Validación de Parámetros
# =========================


def require_params(data, *params):
    """
    Valida que existan parámetros requeridos en un dict.

    Args:
        data: dict con parámetros (request.GET, request.POST, json.loads(request.body))
        *params: nombres de parámetros requeridos

    Returns:
        tuple: (ok: bool, missing: list)

    Uso:
        data = json.loads(request.body)
        ok, missing = require_params(data, "nombre", "marca_id")
        if not ok:
            return bad(f"Faltan parámetros: {', '.join(missing)}")
    """
    missing = [p for p in params if not data.get(p)]
    return (len(missing) == 0, missing)


# =========================
# Ejemplo de Uso Completo
# =========================

# """
# # En views_fbv.py

# from .api_helpers import ok, bad, ajax_get, ajax_post, get_user_scope, parse_int

# @ajax_get
# def ajax_modelos_por_marca_anio(request):
#     marca_id = request.GET.get("marca_id")
#     if not marca_id:
#         return bad("Falta parámetro 'marca_id'")

#     try:
#         marca_id = parse_int(marca_id, "marca_id")
#     except ValueError as e:
#         return bad(str(e))

#     empresa, pais = get_user_scope(request)

#     # Validar que marca pertenece al país
#     try:
#         marca = Marca.objects.get(pk=marca_id, country=pais)
#     except Marca.DoesNotExist:
#         return bad("Marca no encontrada en tu país", status=404)

#     # Filtrar modelos
#     qs = Modelo.objects.filter(marca_id=marca.pk, country=pais)

#     # Scoping por empresa (si aplica)
#     if hasattr(Modelo, "empresa") and empresa:
#         qs = qs.filter(empresa=empresa)

#     modelos = [{"id": str(m.pk), "nombre": m.nombre} for m in qs.order_by("nombre")]
#     return ok(modelos=modelos)


# @ajax_post_staff
# def ajax_agregar_marca(request):
#     import json
#     data = json.loads(request.body)

#     ok_params, missing = require_params(data, "nombre")
#     if not ok_params:
#         return bad(f"Faltan parámetros: {', '.join(missing)}")

#     nombre = data["nombre"].strip()
#     if not nombre:
#         return bad("El nombre no puede estar vacío")

#     empresa, pais = get_user_scope(request)

#     kwargs = {"nombre": nombre, "country": pais}
#     if hasattr(Marca, "empresa") and empresa:
#         kwargs["empresa"] = empresa

#     marca, created = Marca.objects.get_or_create(**kwargs)

#     return ok(
#         marca={"id": str(marca.pk), "nombre": marca.nombre},
#         created=created
#     )
# """
