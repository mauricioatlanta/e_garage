from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db.models import ObjectDoesNotExist
from django.apps import apps


def get_user_empresa_safe(user):
    """
    Obtiene la empresa del usuario sin lanzar si no existe.
    La relación OneToOne inversa (user.empresa) lanza ObjectDoesNotExist
    cuando no hay Empresa; getattr() no lo captura.
    """
    if not user or not getattr(user, "is_authenticated", False):
        return None
    try:
        return user.empresa
    except ObjectDoesNotExist:
        return None


def get_or_create_empresa(request):
    """Obtiene la Empresa asociada al request de forma robusta.

    - Usa request.empresa si un middleware ya la setea.
    - Requiere usuario autenticado; opcionalmente usa DEMO_EMPRESA_ID.
    - Crea una Empresa mínima asociada al usuario si no existe.
    """
    # 1) Empresa desde middleware
    emw = getattr(request, "empresa", None)
    if emw is not None:
        return emw

    user = getattr(request, "user", None)

    # 2) Usuario autenticado o DEMO
    if not user or not getattr(user, "is_authenticated", False):
        demo_id = getattr(settings, "DEMO_EMPRESA_ID", None)
        if demo_id:
            from taller.models.empresa import Empresa

            try:
                return Empresa.objects.get(pk=demo_id)
            except Empresa.DoesNotExist:
                pass
        raise PermissionDenied("Debes iniciar sesión para ver este reporte.")

    # 3) Intentar relación directa (evitar DoesNotExist de la OneToOne inversa)
    empresa = get_user_empresa_safe(user)
    if empresa is not None:
        return empresa

    # 4) Buscar por FK y crear si no existe
    from taller.models.empresa import Empresa

    empresa = Empresa.objects.filter(user=user).first()
    if empresa:
        return empresa

    empresa, _ = Empresa.objects.get_or_create(
        user=user,
        defaults={
            "nombre_taller": f"Taller {getattr(user, 'username', 'Usuario')}",
            "direccion": "N/A",
            "telefono": "N/A",
            "email": getattr(user, "email", "demo@ejemplo.com"),
        },
    )
    return empresa


def get_active_empresa(request):
    """
    Devuelve la empresa activa:
    Fuente única de verdad (evitar mezcla session vs user.empresa):
    1) request.empresa (si un middleware ya la setea)
    2) user.empresa (OneToOne) de forma segura

    Nota: si existe session/GET 'empresa_id', solo se usa si coincide con la
    empresa real del usuario (para compatibilidad), de lo contrario se ignora.
    """
    if not request.user.is_authenticated:
        return None

    empresa_from_mw = getattr(request, "empresa", None)
    if empresa_from_mw is not None:
        return empresa_from_mw

    empresa = get_user_empresa_safe(request.user)
    if empresa is None:
        Empresa = apps.get_model("taller", "Empresa")
        empresa = Empresa.objects.filter(user=request.user).order_by("id").first()
        if empresa is None:
            return None

    empresa_id = request.session.get("empresa_id") or request.GET.get("empresa_id")
    if empresa_id and str(empresa_id) != str(empresa.id):
        return empresa

    return empresa
