"""
Vistas country-aware para documentos usando patrón COMMON + país.

Estas vistas usan select_template para permitir override por país
con fallback automático a las plantillas comunes.
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import select_template
from django.contrib import messages
from django.db import transaction

from taller.configuracion.rubros_logic import (
    get_responsable_label,
    get_roles_permitidos,
    get_ui_config,
)
from taller.models.documento import Documento
from taller.models.tecnico import Tecnico
from taller.documentos.forms import DocumentoForm


def _tecnicos_queryset_for_empresa(empresa, roles_permitidos=None):
    """
    Obtiene el queryset de técnicos filtrado según el rubro de la empresa.
    """
    if not empresa:
        return Tecnico.objects.none()

    if not roles_permitidos:
        roles_permitidos = ['TECNICO', 'VENDEDOR', 'MIXTO']

    return Tecnico.objects.filter(
        empresa=empresa,
        activo=True,
        rol__in=roles_permitidos,
    ).order_by("nombre")


@login_required
def documentos_listar(request, country_code="cl", lang_code="es"):
    """
    Lista documentos usando patrón COMMON + país.

    Args:
        country_code: Código del país (cl, us, mx, pe, co, ec, ve, br)
        lang_code: Código del idioma (es, en)
    """
    empresa = getattr(request.user, "empresa", None)
    if not empresa:
        messages.error(request, "Usuario sin empresa asignada")
        return redirect("/")

    # Filtrar documentos por empresa del usuario
    documentos = (
        Documento.objects.filter(empresa=empresa)
        .select_related("cliente", "vehiculo", "tecnico_responsable", "empresa")
        .order_by("-fecha_emision", "-id")
    )

    # Usar select_template con fallback a common
    template = select_template(
        [
            f"{country_code}/{lang_code}/documentos/lista_documentos.html",
            "taller/common/documentos/lista_documentos.html",
        ]
    )

    return render(
        request,
        template.template.name,
        {
            "documentos": documentos,
            "country_code": country_code,
            "lang_code": lang_code,
            "empresa": empresa,
        },
    )


@login_required
def documento_crear(request, country_code="cl", lang_code="es"):
    """
    Crear documento usando patrón COMMON + país.

    Args:
        country_code: Código del país (cl, us, mx, pe, co, ec, ve, br)
        lang_code: Código del idioma (es, en)
    """
    empresa = getattr(request.user, "empresa", None)
    if not empresa:
        messages.error(request, "Usuario sin empresa asignada")
        return redirect("/")

    config = getattr(empresa, "config", None)
    # Obtener país desde empresa o country_code
    country = getattr(empresa, "pais", country_code.upper() if country_code else "CL")
    responsable_label = get_responsable_label(config)
    roles_permitidos = get_roles_permitidos(config)
    ui_config = get_ui_config(config)
    tecnicos_qs = _tecnicos_queryset_for_empresa(empresa, roles_permitidos)

    if request.method == "POST":
        form = DocumentoForm(request.POST, user=request.user, empresa=empresa, country=country)
        if "tecnico_responsable" in form.fields:
            form.fields["tecnico_responsable"].label = responsable_label
            form.fields["tecnico_responsable"].queryset = tecnicos_qs

        if form.is_valid():
            try:
                with transaction.atomic():
                    documento = form.save(commit=False)
                    documento.empresa = empresa
                    documento.save()

                    messages.success(
                        request,
                        f"Documento {documento.numero_documento or 'sin número'} creado exitosamente",
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
                        "cl": "lista_documentos_cl",
                        "us": "lista_documentos_us",
                        "mx": "lista_documentos_mx",
                        "pe": "lista_documentos_pe",
                        "co": "lista_documentos_co",
                        "ec": "lista_documentos_ec",
                        "ve": "lista_documentos_ve",
                        "br": "lista_documentos_br",
                    }
                    url_name = url_name_map.get(country_code, "lista_documentos_cl")
                    return redirect(f"{namespace}:{url_name}")
            except Exception as e:
                messages.error(request, f"Error al crear documento: {str(e)}")
        else:
            messages.error(request, "Por favor corrige los errores en el formulario")
    else:
        form = DocumentoForm(user=request.user, empresa=empresa, country=country)
        if "tecnico_responsable" in form.fields:
            form.fields["tecnico_responsable"].label = responsable_label
            form.fields["tecnico_responsable"].queryset = tecnicos_qs

    # Usar select_template con fallback a common
    template = select_template(
        [
            f"{country_code}/{lang_code}/documentos/crear_documento.html",
            "taller/common/documentos/document_form.html",
        ]
    )

    # Obtener secciones visibles según el rubro de la empresa
    secciones_visibles = {}
    if config:
        try:
            secciones_visibles = config.get_secciones_visibles()
        except Exception:
            secciones_visibles = {}

    if not secciones_visibles:
        secciones_visibles = {
            "repuestos": ui_config.get("show_repuestos", True),
            "servicios": ui_config.get("show_services", True),
            "otros_servicios": ui_config.get("show_otros_servicios", True),
            "kilometraje": ui_config.get("show_kilometraje", False),
        }

    # Obtener técnicos para el template
    tecnicos = tecnicos_qs

    context = {
        "form": form,
        "titulo_pagina": "Crear documento",
        "titulo_formulario": "Nuevo documento",
        "texto_boton": "Crear documento",
        "country_code": country_code,
        "lang_code": lang_code,
        "empresa": empresa,
        "secciones_visibles": secciones_visibles,
        "tecnicos": tecnicos,
        "company_country": country,
        "responsable_label": responsable_label,
        "ui_config": ui_config,
    }

    return render(request, template.template.name, context)


@login_required
def documento_editar(request, pk, country_code="cl", lang_code="es"):
    """
    Editar documento usando patrón COMMON + país.

    Args:
        pk: ID del documento
        country_code: Código del país (cl, us, mx, pe, co, ec, ve, br)
        lang_code: Código del idioma (es, en)
    """
    empresa = getattr(request.user, "empresa", None)
    documento = get_object_or_404(Documento, pk=pk, empresa=empresa)

    # Obtener país desde empresa o country_code
    country = getattr(empresa, "pais", country_code.upper() if country_code else "CL")
    config = getattr(empresa, "config", None)
    responsable_label = get_responsable_label(config)
    roles_permitidos = get_roles_permitidos(config)
    ui_config = get_ui_config(config)
    tecnicos_qs = _tecnicos_queryset_for_empresa(empresa, roles_permitidos)

    if request.method == "POST":
        form = DocumentoForm(
            request.POST,
            instance=documento,
            user=request.user,
            empresa=empresa,
            country=country,
        )
        if "tecnico_responsable" in form.fields:
            form.fields["tecnico_responsable"].label = responsable_label
            form.fields["tecnico_responsable"].queryset = tecnicos_qs

        if form.is_valid():
            form.save()
            messages.success(request, "Documento actualizado exitosamente")
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
                "cl": "lista_documentos_cl",
                "us": "lista_documentos_us",
                "mx": "lista_documentos_mx",
                "pe": "lista_documentos_pe",
                "co": "lista_documentos_co",
                "ec": "lista_documentos_ec",
                "ve": "lista_documentos_ve",
                "br": "lista_documentos_br",
            }
            url_name = url_name_map.get(country_code, "lista_documentos_cl")
            return redirect(f"{namespace}:{url_name}")
        else:
            messages.error(request, "Por favor corrige los errores en el formulario")
    else:
        form = DocumentoForm(
            instance=documento,
            user=request.user,
            empresa=empresa,
            country=country,
        )
        if "tecnico_responsable" in form.fields:
            form.fields["tecnico_responsable"].label = responsable_label
            form.fields["tecnico_responsable"].queryset = tecnicos_qs

    # Usar select_template con fallback a common
    template = select_template(
        [
            f"{country_code}/{lang_code}/documentos/editar_documento.html",
            "taller/common/documentos/document_form.html",
        ]
    )

    # Obtener secciones visibles según el rubro de la empresa
    secciones_visibles = {}
    if config:
        try:
            secciones_visibles = config.get_secciones_visibles()
        except Exception:
            secciones_visibles = {}

    if not secciones_visibles:
        secciones_visibles = {
            "repuestos": ui_config.get("show_repuestos", True),
            "servicios": ui_config.get("show_services", True),
            "otros_servicios": ui_config.get("show_otros_servicios", True),
            "kilometraje": ui_config.get("show_kilometraje", False),
        }

    # Obtener técnicos para el template
    tecnicos = tecnicos_qs

    context = {
        "form": form,
        "documento": documento,
        "titulo_pagina": "Editar documento",
        "titulo_formulario": "Editar documento",
        "texto_boton": "Guardar cambios",
        "country_code": country_code,
        "lang_code": lang_code,
        "empresa": empresa,
        "secciones_visibles": secciones_visibles,
        "tecnicos": tecnicos,
        "company_country": country,
        "responsable_label": responsable_label,
        "ui_config": ui_config,
    }

    return render(request, template.template.name, context)


@login_required
def documento_ver(request, pk, country_code="cl", lang_code="es"):
    """
    Ver detalle de documento usando patrón COMMON + país.

    Args:
        pk: ID del documento
        country_code: Código del país (cl, us, mx, pe, co, ec, ve, br)
        lang_code: Código del idioma (es, en)
    """
    empresa = getattr(request.user, "empresa", None)
    documento = get_object_or_404(
        Documento.objects.select_related(
            "cliente", "vehiculo", "tecnico_responsable"
        ).prefetch_related("lineas_repuesto", "lineas_servicio", "lineas_otro_servicio"),
        pk=pk,
        empresa=empresa,
    )

    # Usar select_template con fallback a common
    template = select_template(
        [
            f"{country_code}/{lang_code}/documentos/ver_documento.html",
            "taller/common/documentos/ver_documento_nuevo.html",
        ]
    )

    return render(
        request,
        template.template.name,
        {
            "documento": documento,
            "country_code": country_code,
            "lang_code": lang_code,
            "empresa": empresa,
        },
    )
