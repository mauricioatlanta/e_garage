"""
Vistas públicas del storefront individual de cada empresa, y kiosko centralizado.

Acceso sin login.
- Storefront individual: empresa resuelta por slug; solo empresas activa_y_vigente.
- Kiosko centralizado: todas las piezas de empresas con kiosko_autorizado=True y activa_y_vigente.
"""

import re
from urllib.parse import quote

from django.core.paginator import Paginator
from django.db.models import Case, IntegerField, Q, Value, When
from django.db.models.functions import Lower
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from taller.models.alias_repuesto import AliasRepuesto
from taller.models.empresa import Empresa
from taller.models.interchange_pieza import InterchangePieza
from taller.models.pieza_desarme import (
    CONDICION_CHOICES,
    CONDICION_NUEVA,
    ESTADO_DISPONIBLE,
    PiezaDesarme,
)


def _telefono_wa(telefono: str) -> str:
    """Devuelve solo dígitos del teléfono, sin el + inicial."""
    return re.sub(r"\D", "", telefono or "")


def _telefono_tel(telefono: str) -> str:
    """Limpia el teléfono para uso en tel:, preservando el + si existe."""
    return re.sub(r"[^\d+]", "", telefono or "")


def _tienda_storefront_render(request, empresa):
    """Lógica compartida del storefront público de una empresa."""
    if not empresa.activa_y_vigente:
        return render(request, "public/storefront/tienda_inactiva.html", {"empresa": empresa}, status=410)

    q = request.GET.get("q", "").strip()
    anio_sel = request.GET.get("anio", "").strip()
    marca_sel = request.GET.get("marca", "").strip()
    modelo_sel = request.GET.get("modelo", "").strip()
    motor_sel = request.GET.get("motor", "").strip()

    base_qs = PiezaDesarme.objects.filter(
        empresa=empresa,
        estado_pieza=ESTADO_DISPONIBLE,
        activo=True,
    ).select_related(
        "vehiculo_desarme", "vehiculo_desarme__marca",
        "vehiculo_desarme__modelo", "vehiculo_desarme__motor",
    )

    # ── Filtro comercial por marcas permitidas ────────────────────────────────
    _marcas_csv = empresa.marcas_permitidas_catalogo.strip()
    if _marcas_csv:
        _marcas_lower = [m.strip().lower() for m in _marcas_csv.split(",") if m.strip()]
        base_qs = base_qs.annotate(
            _marca_fk_lower=Lower("vehiculo_desarme__marca__nombre"),
            _marca_txt_lower=Lower("vehiculo_desarme__marca_texto"),
        ).filter(
            Q(_marca_fk_lower__in=_marcas_lower) | Q(_marca_txt_lower__in=_marcas_lower)
        )

    # ── Cascada de filtros: anio → marca → modelo → motor ────────────────────
    anios_disponibles = sorted(
        {v for v in base_qs.values_list("vehiculo_desarme__anio", flat=True) if v},
        reverse=True,
    )
    qs_tras_anio = base_qs.filter(vehiculo_desarme__anio=anio_sel) if anio_sel else base_qs

    marcas_rows = qs_tras_anio.values(
        "vehiculo_desarme__marca__nombre", "vehiculo_desarme__marca_texto"
    ).distinct()
    marcas_disponibles = sorted({
        r["vehiculo_desarme__marca__nombre"] or r["vehiculo_desarme__marca_texto"] or ""
        for r in marcas_rows
        if r["vehiculo_desarme__marca__nombre"] or r["vehiculo_desarme__marca_texto"]
    })
    if marca_sel:
        qs_tras_marca = qs_tras_anio.filter(
            Q(vehiculo_desarme__marca__nombre__iexact=marca_sel)
            | Q(vehiculo_desarme__marca_texto__iexact=marca_sel)
        )
    else:
        qs_tras_marca = qs_tras_anio

    modelos_rows = qs_tras_marca.values(
        "vehiculo_desarme__modelo__nombre", "vehiculo_desarme__modelo_texto"
    ).distinct()
    modelos_disponibles = sorted({
        r["vehiculo_desarme__modelo__nombre"] or r["vehiculo_desarme__modelo_texto"] or ""
        for r in modelos_rows
        if r["vehiculo_desarme__modelo__nombre"] or r["vehiculo_desarme__modelo_texto"]
    })
    if modelo_sel:
        qs_tras_modelo = qs_tras_marca.filter(
            Q(vehiculo_desarme__modelo__nombre__iexact=modelo_sel)
            | Q(vehiculo_desarme__modelo_texto__iexact=modelo_sel)
        )
    else:
        qs_tras_modelo = qs_tras_marca

    motores_disponibles = sorted({
        r["vehiculo_desarme__motor__nombre"]
        for r in qs_tras_modelo.values("vehiculo_desarme__motor__nombre").distinct()
        if r["vehiculo_desarme__motor__nombre"]
    })
    piezas_qs = (
        qs_tras_modelo.filter(vehiculo_desarme__motor__nombre__iexact=motor_sel)
        if motor_sel else qs_tras_modelo
    )

    # ── Filtro de texto con aliases ───────────────────────────────────────────
    filtro_texto = None
    if q:
        canonicos = set(
            AliasRepuesto.objects.filter(termino_busqueda__icontains=q)
            .values_list("pieza_canonica", flat=True)
        )
        canonicos.add(q)
        filtro_texto = Q(nombre__icontains=q) | Q(codigo__icontains=q)
        for canon in canonicos:
            filtro_texto |= Q(nombre__icontains=canon)
        piezas_qs = piezas_qs.filter(filtro_texto)

    # ── Expansión por interchange (bidireccional) ─────────────────────────────
    # Busca en ambas direcciones:
    #   A) Mi vehículo aparece como "compatible" → hay piezas de otro origen que sirven en el mío
    #   B) Mi vehículo aparece como "origen" → las mismas piezas también funcionan en compatibles
    # En ambos casos se obtiene el codigo_pieza y se busca ese código en el inventario.
    if marca_sel or modelo_sel:
        anio_int = None
        if anio_sel:
            try:
                anio_int = int(anio_sel)
            except (ValueError, TypeError):
                pass

        # Dirección A: vehículo del usuario es el "compatible"
        ic_compat = Q(empresa=empresa)
        if marca_sel:
            ic_compat &= Q(marca_compatible__iexact=marca_sel)
        if modelo_sel:
            ic_compat &= Q(modelo_compatible__iexact=modelo_sel)
        if anio_int:
            ic_compat &= (
                Q(anio_compatible_desde__lte=anio_int)
                & Q(anio_compatible_hasta__gte=anio_int)
            )

        # Dirección B: vehículo del usuario es el "origen"
        ic_origen = Q(empresa=empresa)
        if marca_sel:
            ic_origen &= Q(marca_origen__iexact=marca_sel)
        if modelo_sel:
            ic_origen &= Q(modelo_origen__iexact=modelo_sel)
        if anio_int:
            ic_origen &= (
                Q(anio_origen_desde__lte=anio_int)
                & Q(anio_origen_hasta__gte=anio_int)
            )

        codigos_ic = set(
            InterchangePieza.objects.filter(ic_compat | ic_origen)
            .values_list("codigo_pieza", flat=True)
        )
        if codigos_ic:
            ic_qs = base_qs.filter(codigo__in=codigos_ic)
            if filtro_texto is not None:
                ic_qs = ic_qs.filter(filtro_texto)
            piezas_qs = base_qs.filter(
                Q(pk__in=piezas_qs.values("pk")) | Q(pk__in=ic_qs.values("pk"))
            ).select_related(
                "vehiculo_desarme", "vehiculo_desarme__marca",
                "vehiculo_desarme__modelo", "vehiculo_desarme__motor",
            )

    piezas_qs = piezas_qs.order_by("-prioridad", "nombre")

    paginator = Paginator(piezas_qs, 24)
    piezas = paginator.get_page(request.GET.get("page", 1))

    tel = _telefono_wa(empresa.telefono)
    tel_url = f"tel:{_telefono_tel(empresa.telefono)}" if empresa.telefono else None
    for pieza in piezas:
        pieza.tel_url = tel_url
        v = pieza.vehiculo_desarme
        pieza.vehiculo_anio_str = str(v.anio) if v and v.anio else ""
        pieza.vehiculo_marcamodelo_str = " ".join(filter(None, [
            v.get_marca_display() if v else None,
            v.get_modelo_display() if v else None,
        ])) if v else ""
        pieza.vehiculo_motor_str = str(v.motor) if v and v.motor else ""
        pieza.vehiculo_label = " ".join(filter(None, [
            pieza.vehiculo_anio_str,
            pieza.vehiculo_marcamodelo_str,
            pieza.vehiculo_motor_str,
        ]))
        if tel:
            msg = f"Hola! Me interesa el repuesto: {pieza.nombre}"
            if pieza.codigo:
                msg += f" (cód. {pieza.codigo})"
            if pieza.vehiculo_label:
                msg += f" — Vehículo: {pieza.vehiculo_label}"
            precio = pieza.precio_venta_sugerido or pieza.precio_sugerido
            if precio:
                msg += f" — Precio: ${precio:,.0f}"
            pieza.wa_url = f"https://wa.me/{tel}?text={quote(msg)}"
        else:
            pieza.wa_url = None

    hay_filtros = bool(q or anio_sel or marca_sel or modelo_sel or motor_sel)
    return render(request, "public/storefront/tienda.html", {
        "empresa": empresa,
        "piezas": piezas,
        "q": q,
        "anio_sel": anio_sel,
        "marca_sel": marca_sel,
        "modelo_sel": modelo_sel,
        "motor_sel": motor_sel,
        "anios_disponibles": anios_disponibles,
        "marcas_disponibles": marcas_disponibles,
        "modelos_disponibles": modelos_disponibles,
        "motores_disponibles": motores_disponibles,
        "hay_filtros": hay_filtros,
        "total": piezas.paginator.count,
    })


def tienda_storefront(request, empresa_id: int):
    """Storefront público por empresa_id (URL legacy). Requiere kiosko_autorizado."""
    empresa = get_object_or_404(
        Empresa.objects.select_related("configuracion_comision"),
        id=empresa_id,
        configuracion_comision__kiosko_autorizado=True,
    )
    return _tienda_storefront_render(request, empresa)


def tienda_storefront_slug(request, slug: str):
    """Storefront público por slug amigable (/tienda/<slug>/). Accesible a cualquier empresa activa."""
    empresa = get_object_or_404(Empresa, slug=slug)
    return _tienda_storefront_render(request, empresa)


def kiosko_centralizado(request):
    """
    Kiosko público centralizado: piezas disponibles de todas las empresas con
    kiosko_autorizado=True y activa_y_vigente=True.

    Filtros en cascada (GET): anio → marca → modelo → q (nombre pieza) → tipo → region
    Orden: piezas de la región seleccionada primero, luego el resto.
    """
    # IDs de empresas elegibles (traduce activa_y_vigente a SQL)
    empresas_ok = Empresa.objects.filter(
        configuracion_comision__kiosko_autorizado=True,
        suscripcion_activa=True,
    ).filter(
        Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=timezone.now())
    ).values_list("id", flat=True)

    # Queryset base: piezas disponibles de empresas autorizadas
    base_qs = PiezaDesarme.objects.filter(
        empresa_id__in=empresas_ok,
        estado_pieza=ESTADO_DISPONIBLE,
        activo=True,
    ).select_related("vehiculo_desarme", "vehiculo_desarme__marca", "vehiculo_desarme__modelo", "empresa")

    # ── Lectura de parámetros GET ──────────────────────────────────────────────
    anio_sel = request.GET.get("anio", "").strip()
    marca_sel = request.GET.get("marca", "").strip()
    modelo_sel = request.GET.get("modelo", "").strip()
    q = request.GET.get("q", "").strip()
    tipo_sel = request.GET.get("tipo", "").strip()   # "NUEVO" | "USADO"
    region_sel = request.GET.get("region", "").strip()

    # ── Opciones de cascada (cada nivel filtra el siguiente) ───────────────────
    # Años disponibles
    anios_disponibles = sorted(
        base_qs.values_list("vehiculo_desarme__anio", flat=True).distinct(),
        reverse=True,
    )

    # Aplicar anio antes de calcular marcas
    qs_tras_anio = base_qs.filter(vehiculo_desarme__anio=anio_sel) if anio_sel else base_qs
    marcas_rows = qs_tras_anio.values("vehiculo_desarme__marca__nombre", "vehiculo_desarme__marca_texto").distinct()
    marcas_disponibles = sorted({
        row["vehiculo_desarme__marca__nombre"] or row["vehiculo_desarme__marca_texto"] or ""
        for row in marcas_rows
        if row["vehiculo_desarme__marca__nombre"] or row["vehiculo_desarme__marca_texto"]
    })

    # Aplicar marca antes de calcular modelos
    if marca_sel:
        qs_tras_marca = qs_tras_anio.filter(
            Q(vehiculo_desarme__marca__nombre__iexact=marca_sel)
            | Q(vehiculo_desarme__marca_texto__iexact=marca_sel)
        )
    else:
        qs_tras_marca = qs_tras_anio
    modelos_rows = qs_tras_marca.values("vehiculo_desarme__modelo__nombre", "vehiculo_desarme__modelo_texto").distinct()
    modelos_disponibles = sorted({
        row["vehiculo_desarme__modelo__nombre"] or row["vehiculo_desarme__modelo_texto"] or ""
        for row in modelos_rows
        if row["vehiculo_desarme__modelo__nombre"] or row["vehiculo_desarme__modelo_texto"]
    })

    # ── Construir queryset final aplicando todos los filtros ───────────────────
    piezas_qs = qs_tras_marca

    if modelo_sel:
        piezas_qs = piezas_qs.filter(
            Q(vehiculo_desarme__modelo__nombre__icontains=modelo_sel)
            | Q(vehiculo_desarme__modelo_texto__icontains=modelo_sel)
        )

    if q:
        piezas_qs = piezas_qs.filter(nombre__icontains=q)

    if tipo_sel == "NUEVO":
        piezas_qs = piezas_qs.filter(condicion=CONDICION_NUEVA)
    elif tipo_sel == "USADO":
        piezas_qs = piezas_qs.exclude(condicion=CONDICION_NUEVA)

    # Regiones disponibles (tras todos los filtros previos, antes de filtrar por región)
    regiones_disponibles = sorted(
        {r for r in piezas_qs.values_list("empresa__region", flat=True).distinct() if r}
    )

    if region_sel:
        piezas_qs = piezas_qs.filter(empresa__region__iexact=region_sel)

    # Orden: piezas de la región seleccionada primero; luego por prioridad y nombre
    if region_sel:
        piezas_qs = piezas_qs.annotate(
            prox=Case(
                When(empresa__region__iexact=region_sel, then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            )
        ).order_by("prox", "-prioridad", "nombre")
    else:
        piezas_qs = piezas_qs.order_by("-prioridad", "nombre")

    # Paginación
    paginator = Paginator(piezas_qs, 24)
    page_num = request.GET.get("page", 1)
    piezas = paginator.get_page(page_num)

    # Pre-calcular wa_url para cada pieza usando el teléfono de su propia empresa
    for pieza in piezas:
        pieza.tel_url = f"tel:{_telefono_tel(pieza.empresa.telefono)}" if pieza.empresa.telefono else None
        tel = _telefono_wa(pieza.empresa.telefono)
        if tel:
            msg = f"Hola! Me interesa el repuesto: {pieza.nombre}"
            if pieza.codigo:
                msg += f" (cód. {pieza.codigo})"
            precio = pieza.precio_venta_sugerido or pieza.precio_sugerido
            if precio:
                msg += f" — Precio: ${precio:,.0f}"
            pieza.wa_url = f"https://wa.me/{tel}?text={quote(msg)}"
        else:
            pieza.wa_url = None

    # Query string para links de paginación (sin el parámetro page)
    qs_parts = []
    if anio_sel:
        qs_parts.append(f"anio={quote(anio_sel)}")
    if marca_sel:
        qs_parts.append(f"marca={quote(marca_sel)}")
    if modelo_sel:
        qs_parts.append(f"modelo={quote(modelo_sel)}")
    if q:
        qs_parts.append(f"q={quote(q)}")
    if tipo_sel:
        qs_parts.append(f"tipo={quote(tipo_sel)}")
    if region_sel:
        qs_parts.append(f"region={quote(region_sel)}")
    qs_base = "&".join(qs_parts)

    return render(request, "public/storefront/kiosko.html", {
        "piezas": piezas,
        "anio_sel": anio_sel,
        "marca_sel": marca_sel,
        "modelo_sel": modelo_sel,
        "q": q,
        "tipo_sel": tipo_sel,
        "region_sel": region_sel,
        "anios_disponibles": anios_disponibles,
        "marcas_disponibles": marcas_disponibles,
        "modelos_disponibles": modelos_disponibles,
        "regiones_disponibles": regiones_disponibles,
        "show_empresa": True,
        "qs_base": qs_base,
    })
