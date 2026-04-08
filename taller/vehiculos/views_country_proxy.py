from contextlib import contextmanager
from functools import wraps

from taller.vehiculos import views_fbv as base_views


PATH_TO_COUNTRY = (
    ("/us/en/", "US"),
    ("/us/es/", "US"),
    ("/us/", "US"),
    ("/cl/es/", "CL"),
    ("/cl/", "CL"),
    ("/mx/es/", "MX"),
    ("/mx/", "MX"),
    ("/pe/es/", "PE"),
    ("/pe/", "PE"),
    ("/co/es/", "CO"),
    ("/co/", "CO"),
    ("/ec/es/", "EC"),
    ("/ec/", "EC"),
    ("/ve/es/", "VE"),
    ("/ve/", "VE"),
    ("/br/pt/", "BR"),
    ("/br/es/", "BR"),
    ("/br/", "BR"),
)


def _detect_country_from_request(request, default="CL"):
    path_lower = (getattr(request, "path", "") or "").lower()
    for prefix, country_code in PATH_TO_COUNTRY:
        if path_lower.startswith(prefix):
            return country_code
    return (default or "CL").strip().upper()


@contextmanager
def _patched_request_country(request):
    target_country = _detect_country_from_request(request)
    empresa = getattr(request.user, "empresa", None)
    original_request_country = getattr(request, "country", None)
    original_request_country_code = getattr(request, "country_code", None)
    original_empresa_pais = getattr(empresa, "pais", None) if empresa else None

    request.country = target_country
    request.country_code = target_country
    if empresa is not None:
        empresa.pais = target_country

    try:
        yield
    finally:
        request.country = original_request_country
        request.country_code = original_request_country_code
        if empresa is not None:
            empresa.pais = original_empresa_pais


def _wrap_country_aware(view_func):
    @wraps(view_func)
    def inner(request, *args, **kwargs):
        with _patched_request_country(request):
            return view_func(request, *args, **kwargs)

    return inner


lista_vehiculos = _wrap_country_aware(base_views.lista_vehiculos)
crear_vehiculo = _wrap_country_aware(base_views.crear_vehiculo)
ver_vehiculo = _wrap_country_aware(base_views.ver_vehiculo)
editar_vehiculo = _wrap_country_aware(base_views.editar_vehiculo)
eliminar_vehiculo = _wrap_country_aware(base_views.eliminar_vehiculo)

api_marcas = _wrap_country_aware(base_views.api_marcas)
api_busqueda_clientes = _wrap_country_aware(base_views.api_busqueda_clientes)
api_colores = _wrap_country_aware(base_views.api_colores)
api_modelos_usa = _wrap_country_aware(base_views.api_modelos_usa)

ajax_modelos_por_marca = _wrap_country_aware(base_views.ajax_modelos_por_marca)
ajax_modelos_por_marca_anio = _wrap_country_aware(base_views.ajax_modelos_por_marca_anio)
modelos_por_marca_api = _wrap_country_aware(base_views.modelos_por_marca_api)
ajax_motores_por_modelo = _wrap_country_aware(base_views.ajax_motores_por_modelo)
ajax_cajas_por_modelo = _wrap_country_aware(base_views.ajax_cajas_por_modelo)

ajax_agregar_marca = _wrap_country_aware(base_views.ajax_agregar_marca)
ajax_agregar_modelo = _wrap_country_aware(base_views.ajax_agregar_modelo)
ajax_agregar_motor = _wrap_country_aware(base_views.ajax_agregar_motor)
ajax_agregar_caja = _wrap_country_aware(base_views.ajax_agregar_caja)
ajax_agregar_color = _wrap_country_aware(base_views.ajax_agregar_color)
