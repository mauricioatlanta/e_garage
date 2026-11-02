from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def crear_marca(request):
    """Vista para crear nueva marca en popup"""
    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        if not nombre:
            messages.error(request, "El nombre de la marca es requerido")
        else:
            from django.db import transaction

            from taller.models.marca import Marca

            try:
                with transaction.atomic():
                    # Obtener país de la empresa del usuario
                    country = getattr(request.user.empresa, "pais", "CL")

                    marca, created = Marca.objects.get_or_create(
                        nombre=nombre, country=country, defaults={"activa": True}
                    )

                    if created:
                        messages.success(request, f"Marca '{nombre}' creada exitosamente")
                    else:
                        messages.info(request, f"La marca '{nombre}' ya existe")

                    # Enviar postMessage al opener
                    return render(
                        request,
                        "taller/vehiculos/close_and_notify.html",
                        {"kind": "marca", "id": marca.id, "text": str(marca)},
                    )

            except Exception as e:
                messages.error(request, f"Error al crear la marca: {str(e)}")

    return render(request, "taller/vehiculos/crear_marca_simple.html")


@login_required
def crear_modelo(request):
    """Vista para crear nuevo modelo en popup"""
    marca_id = request.GET.get("marca", "")

    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        anio = request.POST.get("anio", "").strip()
        marca_id = request.POST.get("marca_id", "").strip()

        if not nombre or not anio or not marca_id:
            messages.error(request, "Todos los campos son requeridos")
        else:
            from django.db import transaction

            from taller.models.marca import Marca
            from taller.models.vehiculos import Modelo

            try:
                with transaction.atomic():
                    marca = Marca.objects.get(id=marca_id)
                    country = getattr(request.user.empresa, "pais", "CL")

                    modelo, created = Modelo.objects.get_or_create(
                        nombre=nombre,
                        anio=int(anio),
                        marca=marca,
                        country=country,
                        defaults={"activo": True},
                    )

                    if created:
                        messages.success(request, f"Modelo '{nombre}' creado exitosamente")
                    else:
                        messages.info(request, f"El modelo '{nombre}' ya existe")

                    # Enviar postMessage al opener
                    return render(
                        request,
                        "taller/vehiculos/close_and_notify.html",
                        {"kind": "modelo", "id": modelo.id, "text": str(modelo)},
                    )

            except Exception as e:
                messages.error(request, f"Error al crear el modelo: {str(e)}")

    # Obtener marcas para el select
    from taller.models.marca import Marca

    country = getattr(request.user.empresa, "pais", "CL")
    marcas = Marca.objects.filter(country=country, activa=True).order_by("nombre")

    return render(
        request,
        "taller/vehiculos/crear_modelo_simple.html",
        {"marcas": marcas, "marca_seleccionada": marca_id},
    )


@login_required
def crear_color(request):
    """Vista para crear nuevo color en popup"""
    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        hex_color = request.POST.get("hex", "").strip().upper()

        if not nombre:
            messages.error(request, "El nombre del color es requerido")
        else:
            import re

            from django.db import transaction

            from taller.models.extras_vehiculo import ColorVehiculo

            try:
                with transaction.atomic():
                    # Validar formato hex si se proporciona
                    if hex_color and not re.match(
                        r"^#([0-9a-f]{3}|[0-9a-f]{6})$", hex_color, re.IGNORECASE
                    ):
                        hex_color = None

                    color, created = ColorVehiculo.objects.get_or_create(
                        nombre=nombre,
                        empresa=request.user.empresa,
                        defaults={"hex": hex_color},
                    )

                    if created:
                        messages.success(request, f"Color '{nombre}' creado exitosamente")
                    else:
                        messages.info(request, f"El color '{nombre}' ya existe")

                    # Enviar postMessage al opener
                    text = f"{color.nombre}"
                    if color.hex:
                        text += f" {color.hex}"

                    return render(
                        request,
                        "taller/vehiculos/close_and_notify.html",
                        {"kind": "color", "id": color.id, "text": text},
                    )

            except Exception as e:
                messages.error(request, f"Error al crear el color: {str(e)}")

    return render(request, "taller/vehiculos/crear_color_simple.html")
