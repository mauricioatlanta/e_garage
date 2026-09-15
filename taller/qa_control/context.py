from django.conf import settings

from taller.models.configuracion import ConfiguracionEmpresa
from taller.models.empresa import Empresa

from .auth import is_control_tower_user


QA_SESSION_KEY = "qa_control"

def _clear(request):
    session = getattr(request, "session", None)
    if session is not None:
        session.pop(QA_SESSION_KEY, None)
        session.modified = True


def clear_qa_control_context(request):
    _clear(request)


def get_qa_control_context(request):
    if not is_control_tower_user(getattr(request, "user", None)):
        _clear(request)
        return None
    context = (getattr(request, "session", {}) or {}).get(QA_SESSION_KEY)
    if context is None:
        return None
    if not isinstance(context, dict):
        _clear(request)
        return None
    return context


def _config_for(empresa):
    try:
        return empresa.config
    except ConfiguracionEmpresa.DoesNotExist:
        return None


def _qa_tenant_matrix():
    return getattr(settings, "QA_CONTROL_TENANTS", {}) or {}


def is_qa_empresa(empresa):
    """Return True only when the exact country/rubro/id tuple is allowlisted."""
    if not empresa or not getattr(empresa, "suscripcion_activa", False):
        return False
    config = _config_for(empresa)
    key = (
        str(getattr(empresa, "pais", "") or "").strip().upper(),
        str(getattr(config, "rubro_principal", "") or "").strip().upper(),
    )
    return str(_qa_tenant_matrix().get(key, "")) == str(empresa.pk)


def _valid_context(request, context):
    if not context or context.get("user_id") != getattr(request.user, "pk", None):
        return None

    try:
        empresa = Empresa.objects.select_related("config").get(pk=context.get("empresa_id"))
    except (Empresa.DoesNotExist, TypeError, ValueError):
        return None

    country = str(context.get("country") or "").strip().upper()
    rubro = str(context.get("rubro") or "").strip().upper()
    config = _config_for(empresa)
    if not config or not is_qa_empresa(empresa):
        return None
    if str(getattr(empresa, "pais", "") or "").strip().upper() != country:
        return None
    if str(getattr(config, "rubro_principal", "") or "").strip().upper() != rubro:
        return None
    return {"country": country, "rubro": rubro, "empresa_id": empresa.pk, "user_id": request.user.pk}


def resolve_qa_empresa(request):
    context = get_qa_control_context(request)
    valid = _valid_context(request, context)
    if valid is None:
        if context:
            _clear(request)
        return None
    try:
        return Empresa.objects.get(pk=valid["empresa_id"])
    except Empresa.DoesNotExist:
        _clear(request)
        return None


def set_qa_control_context(request, empresa):
    if not is_control_tower_user(getattr(request, "user", None)):
        _clear(request)
        return False

    config = _config_for(empresa)
    country = str(getattr(empresa, "pais", "") or "").strip().upper()
    rubro = str(getattr(config, "rubro_principal", "") or "").strip().upper()
    if not config or not country or not rubro or not is_qa_empresa(empresa):
        _clear(request)
        return False

    request.session[QA_SESSION_KEY] = {
        "country": country,
        "rubro": rubro,
        "empresa_id": empresa.pk,
        "user_id": request.user.pk,
    }
    request.session.modified = True
    return True


def find_qa_empresas(country, rubro):
    country = str(country or "").strip().upper()
    rubro = str(rubro or "").strip().upper()
    if not country or not rubro:
        return Empresa.objects.none()
    return (
        Empresa.objects.filter(
            pk=_qa_tenant_matrix().get((country, rubro), -1),
            pais__iexact=country,
            config__rubro_principal=rubro,
            suscripcion_activa=True,
        )
        .select_related("config")
        .order_by("nombre_taller", "pk")
    )
