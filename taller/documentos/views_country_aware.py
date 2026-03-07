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
from django.urls import reverse

from taller.configuracion.rubros_logic import (
    get_responsable_label,
    get_roles_permitidos,
    get_ui_config,
)
from taller.models.documento import Documento
from taller.models.tecnico import Tecnico
from taller.documentos.forms import DocumentoForm
from taller.documentos.views_migrated import (
    build_document_list_queryset,
    enrich_documentos_with_totals,
)


def _tecnicos_queryset_for_empresa(empresa, roles_permitidos=None):
    """
    Obtiene el queryset de técnicos filtrado según el rubro de la empresa.
    """
    if not empresa:
        return Tecnico.objects.none()

    if not roles_permitidos:
        roles_permitidos = ["TECNICO", "VENDEDOR", "MIXTO"]

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

    # Queryset con anotaciones de totales para que no se muestren $0 cuando el total en BD no está actualizado
    documentos_qs = build_document_list_queryset(empresa, request)
    documentos = list(documentos_qs)
    enrich_documentos_with_totals(documentos)

    # Usar select_template con fallback a common
    template = select_template(
        [
            f"{country_code}/{lang_code}/documentos/lista_documentos.html",
            "taller/common/documentos/lista_documentos.html",
        ]
    )

    country = (getattr(empresa, "pais", None) or country_code or "CL").upper().lower()
    # KPIs mínimos para que el template común no falle (lista completa en DocumentoListView)
    estadisticas = {
        "total": len(documentos),
        "total_monto": None,
        "emitidos": 0,
        "borradores": 0,
        "hoy": 0,
        "pendientes_pago": 0,
        "presupuestos_pendientes": 0,
        "ots_sin_cerrar": 0,
        "ultimos_30_dias": 0,
    }

    return render(
        request,
        template.template.name,
        {
            "documentos": documentos,
            "country": country,
            "country_code": country_code,
            "lang_code": lang_code,
            "empresa": empresa,
            "estadisticas": estadisticas,
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
    # País desde path (country_code en URL) primero, luego empresa
    from taller.utils import get_country_from_request

    country = get_country_from_request(
        request, default=getattr(empresa, "pais", country_code.upper() if country_code else "CL")
    )
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

                    # Detectar garantía automáticamente después de guardar
                    # Nota: El registro de kilometraje se crea en el método save() del formulario,
                    # así que necesitamos recargar el documento para acceder al registro
                    if documento.vehiculo:
                        try:
                            # Recargar documento para obtener el registro de kilometraje recién creado
                            documento.refresh_from_db()

                            from taller.utils.garantias import obtener_contexto_garantia

                            garantia_context = obtener_contexto_garantia(documento)

                            # Si se detecta una garantía, mostrar mensaje informativo
                            if garantia_context.get("garantia_detectada"):
                                url_verificacion = (
                                    reverse("reportes:verificar_garantia")
                                    + f"?doc_garantia_id={documento.id}&doc_original_id={garantia_context['documento_original'].id}"
                                )
                                if garantia_context.get("dentro_garantia"):
                                    messages.info(
                                        request,
                                        f"⚠️ Garantía detectada: El vehículo está dentro del límite de garantía "
                                        f"({garantia_context.get('kilometros_recorridos', 0)} km recorridos). "
                                        f"<a href='{url_verificacion}' target='_blank'>Ver detalles</a>",
                                    )
                                else:
                                    messages.warning(
                                        request,
                                        f"⚠️ Garantía detectada: El vehículo EXCEDE el límite de garantía "
                                        f"({garantia_context.get('kilometros_recorridos', 0)} km recorridos). "
                                        f"<a href='{url_verificacion}' target='_blank'>Ver detalles</a>",
                                    )
                        except Exception:
                            # Si hay error en la detección, continuar sin mostrar error al usuario
                            pass

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
        # Precargar vehículo si viene ?vehiculo_id=X (desde Centro de Trabajo)
        initial = {}
        vehiculo_id = request.GET.get("vehiculo_id", "").strip()
        if vehiculo_id and vehiculo_id.isdigit():
            from taller.models.vehiculos import Vehiculo

            vehiculo = (
                Vehiculo.objects.filter(empresa=empresa, pk=int(vehiculo_id))
                .select_related("cliente")
                .first()
            )
            if vehiculo:
                initial["vehiculo"] = vehiculo
                initial["cliente"] = vehiculo.cliente

        form = DocumentoForm(
            initial=initial if initial else None,
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
