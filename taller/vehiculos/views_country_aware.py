"""
Vistas country-aware para vehículos usando patrón COMMON + país.

Estas vistas usan select_template para permitir override por país
con fallback automático a las plantillas comunes.
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import select_template
from django.contrib import messages
from django.db import transaction

from taller.models.vehiculos import Vehiculo
from taller.vehiculos.forms import VehiculoForm


def _get_country_from_path(path: str) -> tuple[str, str]:
    """
    Extrae country_code y lang_code desde la URL path.

    Returns:
        tuple: (country_code, lang_code) ej: ("mx", "es"), ("us", "en")
    """
    path_lower = path.lower()

    # Mapeo de prefijos a (country, lang)
    country_map = {
        "/cl/es/": ("cl", "es"),
        "/us/en/": ("us", "en"),
        "/us/es/": ("us", "es"),
        "/pe/es/": ("pe", "es"),
        "/co/es/": ("co", "es"),
        "/ec/es/": ("ec", "es"),
        "/ve/es/": ("ve", "es"),
        "/mx/es/": ("mx", "es"),
        "/br/es/": ("br", "es"),
    }

    # Buscar prefijo más largo primero
    for prefix, (country, lang) in sorted(country_map.items(), key=lambda x: -len(x[0])):
        if path_lower.startswith(prefix):
            return country, lang

    # Fallback: detectar país desde path
    if path_lower.startswith("/us/"):
        return "us", "en"
    elif path_lower.startswith("/cl/"):
        return "cl", "es"
    elif path_lower.startswith("/mx/"):
        return "mx", "es"
    elif path_lower.startswith("/pe/"):
        return "pe", "es"
    elif path_lower.startswith("/co/"):
        return "co", "es"
    elif path_lower.startswith("/ec/"):
        return "ec", "es"
    elif path_lower.startswith("/ve/"):
        return "ve", "es"
    elif path_lower.startswith("/br/"):
        return "br", "es"

    # Default
    return "cl", "es"


@login_required
def vehiculo_listar(request, country_code="cl", lang_code="es"):
    """
    Lista vehículos usando patrón COMMON + país.

    Args:
        country_code: Código del país (cl, us, mx, pe, co, ec, ve, br)
        lang_code: Código del idioma (es, en)
    """
    empresa = getattr(request.user, "empresa", None)
    if not empresa:
        messages.error(request, "Usuario sin empresa asignada")
        return redirect("/")

    vehiculos = (
        Vehiculo.objects.filter(empresa=empresa)
        .select_related("cliente", "marca", "modelo", "motor", "caja", "color")
        .order_by("-id")
    )

    # Usar select_template con fallback a common
    template = select_template(
        [
            f"{country_code}/{lang_code}/vehiculos/lista_vehiculos.html",
            "taller/common/vehiculos/vehiculo_list.html",
        ]
    )

    return render(
        request,
        template.template.name,
        {
            "vehiculos": vehiculos,
            "country_code": country_code,
            "lang_code": lang_code,
        },
    )


@login_required
def vehiculo_crear(request, country_code="cl", lang_code="es"):
    """
    Crear vehículo usando patrón COMMON + país.

    Args:
        country_code: Código del país (cl, us, mx, pe, co, ec, ve, br)
        lang_code: Código del idioma (es, en)
    """
    empresa = getattr(request.user, "empresa", None)
    if not empresa:
        messages.error(request, "Usuario sin empresa asignada")
        return redirect("/")

    if request.method == "POST":
        form = VehiculoForm(request.POST, user=request.user, request=request)

        if form.is_valid():
            try:
                with transaction.atomic():
                    vehiculo = form.save(commit=False)
                    vehiculo.empresa = empresa
                    vehiculo.save()

                    messages.success(
                        request,
                        f"Vehículo {vehiculo.patente or 'sin patente'} creado exitosamente",
                    )
                    # Redirigir usando el namespace del país
                    namespace_map = {
                        "cl": "chile",
                        "us": "usa",
                        "mx": "taller_mexico",
                        "pe": "taller_peru",
                        "co": "taller_colombia",
                        "ec": "taller_ecuador",
                        "ve": "taller_venezuela",
                        "br": "taller_brasil",
                    }
                    namespace = namespace_map.get(country_code, "chile")
                    # Usar el nombre de URL correcto según el país
                    url_name_map = {
                        "cl": "lista_vehiculos_cl",
                        "us": "lista_vehiculos_us",
                        "mx": "lista_vehiculos_mx",
                        "pe": "lista_vehiculos_pe",
                        "co": "lista_vehiculos_co",
                        "ec": "lista_vehiculos_ec",
                        "ve": "lista_vehiculos_ve",
                        "br": "lista_vehiculos_br",
                    }
                    url_name = url_name_map.get(country_code, "lista_vehiculos_cl")
                    return redirect(f"{namespace}:{url_name}")
            except Exception as e:
                messages.error(request, f"Error al crear vehículo: {str(e)}")
        else:
            messages.error(request, "Por favor corrige los errores en el formulario")
    else:
        form = VehiculoForm(user=request.user, request=request)

    # Usar select_template con fallback a common
    template = select_template(
        [
            f"{country_code}/{lang_code}/vehiculos/crear_vehiculo.html",
            "taller/common/vehiculos/vehiculo_form.html",
        ]
    )

    context = {
        "form": form,
        "titulo_pagina": "Crear vehículo",
        "titulo_formulario": "Nuevo vehículo",
        "texto_boton": "Crear vehículo",
        "country_code": country_code,
        "lang_code": lang_code,
    }

    return render(request, template.template.name, context)


@login_required
def vehiculo_editar(request, pk, country_code="cl", lang_code="es"):
    """
    Editar vehículo usando patrón COMMON + país.

    Args:
        pk: ID del vehículo
        country_code: Código del país (cl, us, mx, pe, co, ec, ve, br)
        lang_code: Código del idioma (es, en)
    """
    empresa = getattr(request.user, "empresa", None)
    vehiculo = get_object_or_404(Vehiculo, pk=pk, empresa=empresa)

    if request.method == "POST":
        form = VehiculoForm(request.POST, instance=vehiculo, user=request.user, request=request)

        if form.is_valid():
            form.save()
            messages.success(request, "Vehículo actualizado exitosamente")
            # Redirigir usando el namespace del país
            namespace_map = {
                "cl": "chile",
                "us": "usa",
                "mx": "taller_mexico",
                "pe": "taller_peru",
                "co": "taller_colombia",
                "ec": "taller_ecuador",
                "ve": "taller_venezuela",
                "br": "taller_brasil",
            }
            namespace = namespace_map.get(country_code, "chile")
            # Usar el nombre de URL correcto según el país
            url_name_map = {
                "cl": "lista_vehiculos_cl",
                "us": "lista_vehiculos_us",
                "mx": "lista_vehiculos_mx",
                "pe": "lista_vehiculos_pe",
                "co": "lista_vehiculos_co",
                "ec": "lista_vehiculos_ec",
                "ve": "lista_vehiculos_ve",
                "br": "lista_vehiculos_br",
            }
            url_name = url_name_map.get(country_code, "lista_vehiculos_cl")
            return redirect(f"{namespace}:{url_name}")
        else:
            messages.error(request, "Por favor corrige los errores en el formulario")
    else:
        form = VehiculoForm(instance=vehiculo, user=request.user, request=request)

    # Usar select_template con fallback a common
    template = select_template(
        [
            f"{country_code}/{lang_code}/vehiculos/editar_vehiculo.html",
            "taller/common/vehiculos/vehiculo_form.html",
        ]
    )

    context = {
        "form": form,
        "vehiculo": vehiculo,
        "titulo_pagina": "Editar vehículo",
        "titulo_formulario": "Editar vehículo",
        "texto_boton": "Guardar cambios",
        "country_code": country_code,
        "lang_code": lang_code,
    }

    return render(request, template.template.name, context)


@login_required
def vehiculo_detalle(request, pk, country_code="cl", lang_code="es"):
    """
    Ver detalle de vehículo usando patrón COMMON + país.

    Args:
        pk: ID del vehículo
        country_code: Código del país (cl, us, mx, pe, co, ec, ve, br)
        lang_code: Código del idioma (es, en)
    """
    empresa = getattr(request.user, "empresa", None)
    vehiculo = get_object_or_404(Vehiculo, pk=pk, empresa=empresa)

    # Usar select_template con fallback a common
    template = select_template(
        [
            f"{country_code}/{lang_code}/vehiculos/detalle_vehiculo.html",
            "taller/common/vehiculos/vehiculo_detail.html",
        ]
    )

    return render(
        request,
        template.template.name,
        {
            "vehiculo": vehiculo,
            "country_code": country_code,
            "lang_code": lang_code,
        },
    )


# Nota: Ya no necesitamos funciones wrapper específicas por país.
# Las URLs pasan country_code y lang_code directamente como parámetros.
