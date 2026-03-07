from django.conf import settings
from django.core.exceptions import PermissionDenied


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

    # 3) Intentar relación directa (OneToOne reverse puede lanzar DoesNotExist si no hay Empresa)
    from django.core.exceptions import ObjectDoesNotExist
    from taller.models.empresa import Empresa

    try:
        empresa = getattr(user, "empresa", None)
        if empresa is not None:
            return empresa
    except (Empresa.DoesNotExist, ObjectDoesNotExist):
        pass

    # 4) Buscar por FK y crear si no existe
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
            "is_trial": True,
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


def ensure_empresa_matches_url_country(request, url_country: str) -> None:
    """
    Alinea session empresa_id con el país de la URL para evitar 403/redirect
    cuando el usuario entra a /us/en/... pero su empresa activa es CL.

    Lógica:
      - Si empresa actual (session o user.empresa) tiene pais == url_country → OK
      - Si no, buscar empresa del usuario con pais=url_country y setear session
      - Superuser: si el usuario no tiene empresa en ese país, usar primera disponible
    """
    if not request.user.is_authenticated or not url_country:
        return

    url_country = (url_country or "").strip().upper()
    if url_country not in ("US", "CL", "MX"):
        return

    emp = get_active_empresa(request)
    if emp and (getattr(emp, "pais", None) or "").strip().upper() == url_country:
        return

    emp2 = Empresa.objects.filter(user=request.user, pais=url_country).first()
    if not emp2 and request.user.is_superuser:
        emp2 = Empresa.objects.filter(pais=url_country).first()

    if emp2:
        request.session["empresa_id"] = emp2.id
        request.session.modified = True
