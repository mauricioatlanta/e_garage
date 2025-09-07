from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from taller.models.repuesto import Repuesto


@login_required
def api_repuesto_por_codigo(request):
    """API para obtener repuesto por código"""
    code = request.GET.get("codigo", "").strip()
    data = {}
    if code:
        try:
            r = Repuesto.objects.get(
                empresa=request.user.empresa, part_number__iexact=code
            )
            data = {
                "id": r.id,
                "nombre": r.nombre,
                "precio_compra": str(r.precio_compra or 0),
                "precio_venta": str(r.precio_venta or 0),
            }
        except Repuesto.DoesNotExist:
            data = {"id": None}
    return JsonResponse(data)
