from django.core.exceptions import PermissionDenied


def empresa_del_request(request):
    empresa = getattr(request, "empresa", None) or getattr(request.user, "empresa", None)
    if not request.user.is_authenticated or not empresa:
        raise PermissionDenied("Usuario sin empresa asignada")
    return empresa


def ensure_order_access(request, order, *, driver_only=False):
    empresa = empresa_del_request(request)
    if order.empresa_id != empresa.id:
        raise PermissionDenied("La orden no pertenece a tu empresa")
    if driver_only:
        if not order.assignments.filter(driver__user=request.user, is_active=True).exists():
            raise PermissionDenied("La orden no está asignada a este conductor")
    return empresa


def ensure_related_company(empresa, *objects):
    for obj in objects:
        if obj is not None and getattr(obj, "empresa_id", empresa.id) != empresa.id:
            raise PermissionDenied("No se pueden mezclar registros de empresas distintas")
