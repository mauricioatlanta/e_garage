"""
Vistas para el Centro de Trabajo / Recepción Vehicular.

Nueva pantalla principal post-login: workspace operativo centrado en el vehículo.
Búsqueda por patente, historial en cards, acción rápida "Ingresar nuevo servicio".
"""

import logging
from django.db.models import prefetch_related_objects
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.urls import reverse

from taller.auth.decorators import country_login_required
from taller.models import Documento, Vehiculo
from taller.utils.ocr import normalizar_patente
from taller.utils.templates import select_country_lang_template

logger = logging.getLogger(__name__)


@country_login_required
def centro_trabajo(request):
    """
    Centro de Trabajo / Recepción Vehicular.
    Pantalla principal post-login: búsqueda por patente y acciones rápidas.
    """
    try:
        empresa = request.user.empresa
    except Exception:
        if "/us/" in (request.path or ""):
            return redirect("usa:configuracion")
        return redirect("chile:configuracion")

    # Vehículos recientes (últimos documentos por empresa)
    docs_recientes = (
        Documento.objects.filter(empresa=empresa)
        .select_related("vehiculo", "cliente")
        .exclude(vehiculo__isnull=True)
        .order_by("-fecha_emision")[:8]
    )
    vehiculos_recientes = []
    vistos = set()
    for doc in docs_recientes:
        if doc.vehiculo_id and doc.vehiculo_id not in vistos:
            vistos.add(doc.vehiculo_id)
            vehiculos_recientes.append(doc.vehiculo)
        if len(vehiculos_recientes) >= 6:
            break

    # URLs base para historial (según país)
    path = request.path or ""
    ns = "usa" if "/us/" in path else "chile"
    vehiculos_con_url = []
    for v in vehiculos_recientes:
        url_hist = reverse(f"{ns}:vehiculo_historial", kwargs={"vehiculo_id": v.pk})
        vehiculos_con_url.append({"vehiculo": v, "url_historial": url_hist})

    hoy = timezone.localdate()
    lang = getattr(request, "LANGUAGE_CODE", "es") or "es"
    pais = getattr(empresa, "pais", "cl") or "cl"

    # URLs según país para el template (usar namespace con idioma para /us/en/ y /us/es/)
    path = request.path or ""
    if "/us/en/" in path or path == "/us/en":
        url_buscar = reverse("us_en:centro_trabajo_buscar")
        url_centro_ops = reverse("us_en:centro_operaciones")
        url_lista_docs = reverse("usa:lista_documentos_us")
        url_crear_veh = reverse("us_en:vehiculos:crear_vehiculo")
        url_lista_veh = reverse("us_en:vehiculos:lista_vehiculos")
        url_lista_clientes = reverse("us_en:clientes:lista_clientes")
        url_settings = reverse("us_en:company_settings")  # /us/en/settings/
    elif "/us/es/" in path or path == "/us/es":
        url_buscar = reverse("us_es:centro_trabajo_buscar")
        url_centro_ops = reverse("us_es:centro_operaciones")
        url_lista_docs = reverse("usa:lista_documentos_us")
        url_crear_veh = reverse("us_es:vehiculos:crear_vehiculo")
        url_lista_veh = reverse("us_es:vehiculos:lista_vehiculos")
        url_lista_clientes = reverse("us_es:clientes:lista_clientes")
        url_settings = reverse("us_es:company_settings")  # /us/es/settings/
    elif "/us/" in path:
        url_buscar = reverse("usa:centro_trabajo_buscar")
        url_centro_ops = reverse("usa:centro_operaciones")
        url_lista_docs = reverse("usa:lista_documentos_us")
        url_crear_veh = reverse("usa:vehiculos:crear_vehiculo")
        url_lista_veh = reverse("usa:vehiculos:lista_vehiculos")
        url_lista_clientes = reverse("usa:clientes:lista_clientes")
        url_settings = reverse("usa:company_settings")
    else:
        url_buscar = reverse("chile:centro_trabajo_buscar")
        url_centro_ops = reverse("chile:centro_operaciones")
        url_lista_docs = reverse("chile:lista_documentos_cl")
        url_crear_veh = reverse("chile:vehiculos:crear_vehiculo")
        url_lista_veh = reverse("chile:vehiculos:lista_vehiculos")
        url_lista_clientes = reverse("chile:clientes:lista_clientes")
        url_settings = reverse("chile:company_settings")

    context = {
        "empresa": empresa,
        "vehiculos_recientes": vehiculos_recientes,
        "vehiculos_con_url": vehiculos_con_url,
        "fecha_hoy": hoy,
        "url_buscar": url_buscar,
        "url_centro_operaciones": url_centro_ops,
        "url_lista_documentos": url_lista_docs,
        "url_crear_vehiculo": url_crear_veh,
        "url_lista_vehiculos": url_lista_veh,
        "url_lista_clientes": url_lista_clientes,
        "url_settings": url_settings,
    }

    template_name = select_country_lang_template(
        "dashboard/centro_trabajo.html",
        pais.lower(),
        lang,
    )
    try:
        from django.template.loader import get_template

        get_template(template_name)
    except Exception:
        template_name = "taller/common/dashboard/centro_trabajo.html"

    return render(request, template_name, context)


@country_login_required
def centro_trabajo_buscar(request):
    """
    Búsqueda de vehículo por patente.
    Redirige a historial si existe, o muestra "no encontrado" con opción de crear.
    """
    patente_raw = (request.GET.get("patente") or request.POST.get("patente") or "").strip()
    if not patente_raw:
        # Sin patente: volver al centro de trabajo
        path = request.path or ""
        if "/us/" in path:
            return redirect("usa:centro_trabajo")
        return redirect("chile:centro_trabajo")

    patente = normalizar_patente(patente_raw)
    try:
        empresa = request.user.empresa
    except Exception:
        if "/us/" in (request.path or ""):
            return redirect("usa:configuracion")
        return redirect("chile:configuracion")

    # Búsqueda exacta por patente normalizada (multi-tenant)
    vehiculo = (
        Vehiculo.objects.filter(empresa=empresa)
        .filter(patente__iexact=patente)
        .select_related("cliente", "marca", "modelo", "color", "motor", "caja")
        .first()
    )

    path = request.path or ""
    if "/us/" in path:
        ns = "usa"
    else:
        ns = "chile"

    if vehiculo:
        return redirect(f"{ns}:vehiculo_historial", vehiculo_id=vehiculo.pk)

    # No encontrado: mostrar template con opción de crear
    crear_url = reverse(f"{ns}:vehiculos:crear_vehiculo")
    if patente_raw:
        crear_url = f"{crear_url}?patente={patente_raw}"
    context = {
        "empresa": empresa,
        "patente_ingresada": patente,
        "patente_raw": patente_raw,
        "crear_vehiculo_url": crear_url,
        "url_centro_trabajo": reverse(f"{ns}:centro_trabajo"),
    }
    template_name = select_country_lang_template(
        "dashboard/vehiculo_no_encontrado.html",
        getattr(empresa, "pais", "cl").lower(),
        getattr(request, "LANGUAGE_CODE", "es") or "es",
    )
    try:
        from django.template.loader import get_template

        get_template(template_name)
    except Exception:
        template_name = "taller/common/dashboard/vehiculo_no_encontrado.html"

    return render(request, template_name, context)


@country_login_required
def vehiculo_historial(request, vehiculo_id):
    """
    Ficha del vehículo + historial en cards.
    Una card por documento/ingreso. Botón principal: Ingresar nuevo servicio.
    """
    try:
        empresa = request.user.empresa
    except Exception:
        if "/us/" in (request.path or ""):
            return redirect("usa:configuracion")
        return redirect("chile:configuracion")

    vehiculo = get_object_or_404(
        Vehiculo.objects.select_related(
            "cliente", "marca", "modelo", "color", "motor", "caja"
        ).filter(empresa=empresa),
        pk=vehiculo_id,
    )

    # Historial: documentos del vehículo ordenados por fecha_emision desc
    path = request.path or ""
    ns = "usa" if "/us/" in path else "chile"

    documentos = (
        Documento.objects.filter(vehiculo=vehiculo, empresa=empresa)
        .select_related("cliente", "vehiculo", "tecnico_responsable")
        .prefetch_related(
            "lineas_servicio", "lineas_servicio__servicio", "lineas_servicio__service"
        )
        .prefetch_related("lineas_repuesto", "lineas_repuesto__repuesto")
        .order_by("-fecha_emision")
    )
    docs_list = list(documentos)

    # Enriquecer cada doc con resumen de servicios y repuestos
    from decimal import Decimal

    for doc in docs_list:
        servicios = [ls.nombre or "" for ls in doc.lineas_servicio.all() if ls.nombre]
        doc._servicios_resumen = servicios[:5]
        doc._servicios_extra = max(0, len(servicios) - 5)

        repuestos = [lr.nombre or "" for lr in doc.lineas_repuesto.all() if lr.nombre]
        doc._repuestos_resumen = repuestos[:5]
        doc._repuestos_extra = max(0, len(repuestos) - 5)

        total_srv = sum(
            (ls.precio_unitario or Decimal("0")) * (ls.cantidad or 0)
            for ls in doc.lineas_servicio.all()
        )
        total_rep = sum(
            (lr.precio_unitario or Decimal("0")) * (lr.cantidad or 0)
            for lr in doc.lineas_repuesto.all()
        )
        doc._total_doc = total_srv + total_rep
        doc._url_ver = reverse(
            f"{ns}:editar_documento_cl" if ns == "chile" else "usa:ver_documento_us",
            kwargs={"pk": doc.pk},
        )
    if ns == "usa":
        crear_doc_url = reverse("usa:crear_documento_us") + f"?vehiculo_id={vehiculo.pk}"
        crear_vehiculo_url = reverse("usa:vehiculos:crear_vehiculo")
    else:
        ns = "chile"
        crear_doc_url = reverse("chile:crear_documento_cl") + f"?vehiculo_id={vehiculo.pk}"
        crear_vehiculo_url = reverse("chile:vehiculos:crear_vehiculo")

    context = {
        "empresa": empresa,
        "vehiculo": vehiculo,
        "documentos": docs_list,
        "crear_documento_url": crear_doc_url,
        "crear_vehiculo_url": crear_vehiculo_url,
        "url_centro_trabajo": reverse(f"{ns}:centro_trabajo"),
        "country_namespace": ns,
    }

    template_name = select_country_lang_template(
        "dashboard/vehiculo_historial.html",
        getattr(empresa, "pais", "cl").lower(),
        getattr(request, "LANGUAGE_CODE", "es") or "es",
    )
    try:
        from django.template.loader import get_template

        get_template(template_name)
    except Exception:
        template_name = "taller/common/dashboard/vehiculo_historial.html"

    return render(request, template_name, context)
