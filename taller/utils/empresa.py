from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db.models import ObjectDoesNotExist


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
            "direccion": "",
            "telefono": "",
            "email": getattr(user, "email", "") or "",
        },
    )
    return empresa


from taller.models import Empresa


def get_active_empresa(request):
    """
    Devuelve la empresa activa:
    1) Session 'empresa_id' (si pertenece al user)
    2) GET ?empresa_id= (si pertenece al user)
    3) Fallback: primera Empresa del user
    """
    if not request.user.is_authenticated:
        return None

    empresa_id = request.session.get("empresa_id") or request.GET.get("empresa_id")
    if empresa_id:
        try:
            # si tu relación es diferente, ajusta el filtro (ej.: owner=request.user)
            return Empresa.objects.get(id=empresa_id, user=request.user)
        except Empresa.DoesNotExist:
            pass

    # Fallback estable
    return Empresa.objects.filter(user=request.user).order_by("id").first()
