from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from taller.servicios.models import CategoriaServicio, Servicio, SubcategoriaServicio


@login_required
@require_GET
def api_servicios_por_categoria(request):
    """
    API para obtener servicios organizados por categorías
    """
    servicios_data = []

    for categoria in CategoriaServicio.objects.all().prefetch_related("subcategorias__servicios"):
        categoria_data = {
            "id": categoria.pk,
            "nombre": categoria.get_label("es"),
            "subcategorias": [],
        }
        for subcategoria in categoria.subcategorias.all():
            subcategoria_data = {
                "id": subcategoria.pk,
                "nombre": subcategoria.get_label("es"),
                "servicios": [],
            }
            for servicio in subcategoria.servicios.all():
                subcategoria_data["servicios"].append(
                    {"id": servicio.pk, "nombre": servicio.get_label("es")}
                )
            categoria_data["subcategorias"].append(subcategoria_data)
        servicios_data.append(categoria_data)

    return JsonResponse({"categorias": servicios_data})


@login_required
@require_GET
def api_buscar_servicios(request):
    """
    API para buscar servicios por nombre
    """
    query = request.GET.get("q", "").strip()

    if len(query) < 2:
        return JsonResponse({"servicios": []})

    servicios = (
        Servicio.objects.filter(names__label__icontains=query)
        .select_related("subcategoria__categoria")
        .distinct()[:20]
    )

    servicios_data = []
    for servicio in servicios:
        nombre = servicio.get_label("es")
        servicios_data.append(
            {
                "id": servicio.id,
                "nombre": nombre,
                "subcategoria": servicio.subcategoria.get_label("es"),
                "categoria": servicio.subcategoria.categoria.get_label("es"),
            }
        )

    return JsonResponse({"servicios": servicios_data})


@login_required
def api_crear_servicio_rapido(request):
    """
    API para crear un servicio rápido cuando no existe en la lista
    """
    if request.method == "POST":
        import json

        data = json.loads(request.body)
        nombre_servicio = data.get("nombre", "").strip()

        if not nombre_servicio:
            return JsonResponse({"error": "Nombre del servicio requerido"}, status=400)

        # Buscar o crear subcategoría "Servicios Personalizados"
        categoria_principal = CategoriaServicio.objects.first()
        if not categoria_principal:
            categoria_principal = CategoriaServicio.objects.create(
                nombre="Servicios de Taller Mecánico"
            )

        subcategoria_custom, created = SubcategoriaServicio.objects.get_or_create(
            categoria=categoria_principal,
            nombre="11. Servicios Personalizados",
            defaults={"categoria": categoria_principal},
        )

        # Crear el servicio
        servicio, created = Servicio.objects.get_or_create(
            subcategoria=subcategoria_custom,
            nombre=nombre_servicio,
            defaults={"subcategoria": subcategoria_custom},
        )

        if created:
            return JsonResponse(
                {
                    "success": True,
                    "servicio": {
                        "id": servicio.pk,
                        "nombre": servicio.get_label("es"),
                        "subcategoria": servicio.subcategoria.get_label("es"),
                    },
                }
            )
        else:
            return JsonResponse(
                {
                    "success": True,
                    "servicio": {
                        "id": servicio.pk,
                        "nombre": servicio.get_label("es"),
                        "subcategoria": servicio.subcategoria.get_label("es"),
                    },
                    "mensaje": "El servicio ya existía",
                }
            )

    return JsonResponse({"error": "Método no permitido"}, status=405)
