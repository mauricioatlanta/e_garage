from django.http import JsonResponse
from .views_listado import DocumentoListViewBase

def lista_debug(request):
    view = DocumentoListViewBase()
    view.request = request
    qs = view.get_queryset()[:20]
    data = []
    for d in qs:
        data.append({
            "id": d.id,
            "numero": getattr(d, "numero", None),
            "country": getattr(d.empresa, "country", None) if hasattr(d, 'empresa') else None,
            "millas": getattr(d, "millas", None),
            "vehiculo_millas": getattr(getattr(d, "vehiculo", None), "millas", None),
            "vehiculo_km": getattr(getattr(d, "vehiculo", None), "kilometraje", None),
            "rep_count": int(getattr(d, "rep_count", 0) or 0),
            "serv_count": int(getattr(d, "serv_count", 0) or 0),
            "otros_count": int(getattr(d, "otros_count", 0) or 0),
            "sum_rep": str(getattr(d, "sum_rep", 0) or 0),
            "sum_serv": str(getattr(d, "sum_serv", 0) or 0),
            "sum_out": str(getattr(d, "sum_out", 0) or 0),
            "total": str(getattr(d, "total", 0) or 0),
        })
    return JsonResponse({"items": data})
