"""
taller/reciclaje/views_staff.py — CRUD de staff del rubro RECYCLING.

Catalitico y ProductoChatarra son SKU con cantidad_stock. Comprar INCREMENTA
cantidad_stock (crea el Catalitico si el código es nuevo); vender DECREMENTA
cantidad_stock, validando que no quede negativo, y marca el Catalitico como
VENDIDO cuando su stock llega a 0.

Protegido con @login_required + @role_required("Owner", "Admin") — mismo
patrón de taller/desarme/views.py. Scoping por empresa manual
(get_user_empresa_safe), no automático.
"""

from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import F
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.dateparse import parse_date

from taller.auth.decorators_role import role_required
from taller.models.clientes import Cliente
from taller.models.reciclaje import (
    Catalitico,
    CompraReciclaje,
    DetalleCompraCatalitico,
    DetalleCompraChatarra,
    DetalleVentaCatalitico,
    DetalleVentaChatarra,
    ProductoChatarra,
    VentaReciclaje,
)
from taller.utils.empresa import get_user_empresa_safe


def _empresa_o_403(request):
    empresa = get_user_empresa_safe(request.user)
    if empresa is None:
        raise PermissionDenied
    return empresa


def _reciclaje_url(suffix: str) -> str:
    """Ruta absoluta al módulo reciclaje. reciclaje_staff vive anidado dentro
    del namespace 'chile' (taller.urls_extra.chile), así que un reverse()
    plano de "reciclaje_staff:..." falla fuera del contexto de template
    (country_url resuelve esto para los enlaces; para redirects en la vista
    basta con la ruta fija, ya que RECYCLING solo está wireado en Chile por
    ahora — mismo patrón que taller/desarme/views.py::_desarme_url)."""
    return f"/cl/es/reciclaje/{suffix.lstrip('/')}"


def _parse_decimal(raw):
    if raw is None or str(raw).strip() == "":
        return None
    text = str(raw).strip().replace("$", "").replace(" ", "")
    if "," in text and "." not in text:
        text = text.replace(",", ".")
    else:
        text = text.replace(",", "")
    try:
        return Decimal(text)
    except InvalidOperation:
        return None


def _resolver_cliente(request, empresa, prefix="cliente"):
    """Resuelve el cliente de una compra/venta: existente por id, uno nuevo
    con los datos mínimos ingresados, o el cliente de mostrador."""
    cliente_id = request.POST.get(f"{prefix}_id")
    if cliente_id:
        return get_object_or_404(Cliente, pk=cliente_id, empresa=empresa)

    nombre = (request.POST.get(f"{prefix}_nuevo_nombre") or "").strip()
    if not nombre:
        return Cliente.get_or_create_mostrador(empresa)

    return Cliente.objects.create(
        empresa=empresa,
        nombre=nombre,
        apellido=(request.POST.get(f"{prefix}_nuevo_apellido") or "").strip(),
        telefono=(request.POST.get(f"{prefix}_nuevo_telefono") or "").strip(),
        tax_id=(request.POST.get(f"{prefix}_nuevo_rut") or "").strip(),
    )


# ── Dashboard ─────────────────────────────────────────────────────────────────


@login_required
@role_required("Owner", "Admin")
def dashboard(request):
    empresa = _empresa_o_403(request)
    catalogo_disponible = Catalitico.objects.filter(
        empresa=empresa, estado=Catalitico.ESTADO_DISPONIBLE, activo=True
    )
    valor_stock = sum(
        (c.precio_venta or Decimal("0")) for c in catalogo_disponible
    )
    context = {
        "total_catalogo_disponible": catalogo_disponible.count(),
        "valor_stock_catalitico": valor_stock,
        "compras_recientes": CompraReciclaje.objects.filter(empresa=empresa)
        .select_related("cliente")
        .order_by("-created_at")[:10],
        "ventas_recientes": VentaReciclaje.objects.filter(empresa=empresa)
        .select_related("comprador")
        .order_by("-created_at")[:10],
        "productos_bajo_stock": ProductoChatarra.objects.filter(
            empresa=empresa,
            activo=True,
            stock_minimo__isnull=False,
            cantidad_stock__lt=F("stock_minimo"),
        ),
    }
    return render(request, "taller/reciclaje/staff/dashboard.html", context)


# ── Compra ────────────────────────────────────────────────────────────────────


@login_required
@role_required("Owner", "Admin")
def crear_compra(request):
    empresa = _empresa_o_403(request)

    if request.method == "POST":
        cliente = _resolver_cliente(request, empresa)

        codigos = request.POST.getlist("catalitico_codigo[]")
        nombres = request.POST.getlist("catalitico_nombre[]")
        marcas = request.POST.getlist("catalitico_marca[]")
        modelos = request.POST.getlist("catalitico_modelo[]")
        cantidades_cat = request.POST.getlist("catalitico_cantidad[]")
        precios_cat = request.POST.getlist("catalitico_precio[]")

        lineas_catalitico = []
        for codigo, nombre, marca, modelo, cantidad_str, precio_str in zip(
            codigos, nombres, marcas, modelos, cantidades_cat, precios_cat, strict=False
        ):
            codigo = (codigo or "").strip()
            cantidad = _parse_decimal(cantidad_str) or Decimal("1")
            precio = _parse_decimal(precio_str)
            if not codigo or precio is None or cantidad <= 0:
                continue
            lineas_catalitico.append(
                {
                    "codigo": codigo,
                    "nombre": (nombre or "").strip(),
                    "marca": (marca or "").strip(),
                    "modelo": (modelo or "").strip(),
                    "cantidad": int(cantidad),
                    "precio": precio,
                }
            )

        producto_ids = request.POST.getlist("chatarra_producto_id[]")
        cantidades = request.POST.getlist("chatarra_cantidad[]")
        precios_cha = request.POST.getlist("chatarra_precio[]")

        lineas_chatarra = []
        for producto_id, cantidad_str, precio_str in zip(
            producto_ids, cantidades, precios_cha, strict=False
        ):
            cantidad = _parse_decimal(cantidad_str)
            precio = _parse_decimal(precio_str)
            if not producto_id or cantidad is None or precio is None or cantidad <= 0:
                continue
            lineas_chatarra.append(
                {"producto_id": producto_id, "cantidad": cantidad, "precio": precio}
            )

        if not lineas_catalitico and not lineas_chatarra:
            messages.error(
                request,
                "Debes ingresar al menos una línea (catalítico o chatarra) para guardar la compra.",
            )
            return redirect(_reciclaje_url("compras/nueva/"))

        codigos_normalizados = [linea["codigo"].lower() for linea in lineas_catalitico]
        errores = []
        if len(codigos_normalizados) != len(set(codigos_normalizados)):
            errores.append(
                "Hay códigos de catalítico repetidos en el formulario — "
                "usa una sola línea por código (súmalos en la cantidad)."
            )
        for linea in lineas_chatarra:
            if not ProductoChatarra.objects.filter(
                pk=linea["producto_id"], empresa=empresa
            ).exists():
                errores.append("Uno de los productos de chatarra seleccionados no es válido.")
                break

        if errores:
            for error in errores:
                messages.error(request, error)
            return redirect(_reciclaje_url("compras/nueva/"))

        with transaction.atomic():
            compra = CompraReciclaje.objects.create(
                empresa=empresa,
                cliente=cliente,
                region_id=request.POST.get("region") or None,
                ciudad_id=request.POST.get("ciudad") or None,
                creado_por=request.user,
                notas=(request.POST.get("notas") or "").strip(),
            )
            for linea in lineas_catalitico:
                catalitico = Catalitico.objects.filter(
                    empresa=empresa, codigo__iexact=linea["codigo"]
                ).first()
                if catalitico is None:
                    catalitico = Catalitico.objects.create(
                        empresa=empresa,
                        codigo=linea["codigo"],
                        nombre=linea["nombre"],
                        marca_vehiculo=linea["marca"],
                        modelo_vehiculo=linea["modelo"],
                        precio_compra=linea["precio"],
                        cantidad_stock=linea["cantidad"],
                        estado=Catalitico.ESTADO_DISPONIBLE,
                    )
                else:
                    # Restock de un código ya catalogado: suma cantidad y
                    # reactiva el estado si estaba agotado (VENDIDO).
                    Catalitico.objects.filter(pk=catalitico.pk).update(
                        cantidad_stock=F("cantidad_stock") + linea["cantidad"],
                        precio_compra=linea["precio"],
                        estado=Catalitico.ESTADO_DISPONIBLE,
                    )
                DetalleCompraCatalitico.objects.create(
                    compra=compra,
                    catalitico=catalitico,
                    cantidad=linea["cantidad"],
                    precio_unitario=linea["precio"],
                )
            for linea in lineas_chatarra:
                producto = get_object_or_404(
                    ProductoChatarra, pk=linea["producto_id"], empresa=empresa
                )
                DetalleCompraChatarra.objects.create(
                    compra=compra,
                    producto=producto,
                    cantidad=linea["cantidad"],
                    precio_unitario=linea["precio"],
                )
                ProductoChatarra.objects.filter(pk=producto.pk).update(
                    cantidad_stock=F("cantidad_stock") + linea["cantidad"]
                )

        total_lineas = len(lineas_catalitico) + len(lineas_chatarra)
        messages.success(request, f"Compra #{compra.pk} registrada con {total_lineas} línea(s).")
        return redirect(_reciclaje_url(f"compras/{compra.pk}/"))

    context = {
        "catalogo_chatarra": ProductoChatarra.objects.filter(
            empresa=empresa, activo=True
        ).order_by("nombre"),
        "clientes": Cliente.objects.filter(empresa=empresa).order_by("nombre")[:200],
    }
    return render(request, "taller/reciclaje/staff/crear_compra.html", context)


@login_required
@role_required("Owner", "Admin")
def listado_compras(request):
    empresa = _empresa_o_403(request)
    compras = (
        CompraReciclaje.objects.filter(empresa=empresa)
        .select_related("cliente")
        .order_by("-created_at")
    )
    page_obj = Paginator(compras, 20).get_page(request.GET.get("page"))
    return render(request, "taller/reciclaje/staff/listado_compras.html", {"page_obj": page_obj})


@login_required
@role_required("Owner", "Admin")
def detalle_compra(request, pk):
    empresa = _empresa_o_403(request)
    compra = get_object_or_404(
        CompraReciclaje.objects.select_related("cliente"), pk=pk, empresa=empresa
    )
    context = {
        "compra": compra,
        "detalles_catalitico": compra.detalles_catalitico.select_related("catalitico"),
        "detalles_chatarra": compra.detalles_chatarra.select_related("producto"),
    }
    return render(request, "taller/reciclaje/staff/detalle_compra.html", context)


# ── Venta ─────────────────────────────────────────────────────────────────────


@login_required
@role_required("Owner", "Admin")
def crear_venta(request):
    empresa = _empresa_o_403(request)

    if request.method == "POST":
        comprador = _resolver_cliente(request, empresa, prefix="comprador")

        catalitico_ids = request.POST.getlist("catalitico_id[]")
        cantidades_cat = request.POST.getlist("catalitico_cantidad[]")
        precios_cat = request.POST.getlist("catalitico_precio[]")
        lineas_catalitico = []
        for catalitico_id, cantidad_str, precio_str in zip(
            catalitico_ids, cantidades_cat, precios_cat, strict=False
        ):
            cantidad = _parse_decimal(cantidad_str) or Decimal("1")
            precio = _parse_decimal(precio_str)
            if not catalitico_id or precio is None or cantidad <= 0:
                continue
            lineas_catalitico.append(
                {"catalitico_id": catalitico_id, "cantidad": int(cantidad), "precio": precio}
            )

        producto_ids = request.POST.getlist("chatarra_producto_id[]")
        cantidades = request.POST.getlist("chatarra_cantidad[]")
        precios_cha = request.POST.getlist("chatarra_precio[]")
        lineas_chatarra = []
        for producto_id, cantidad_str, precio_str in zip(
            producto_ids, cantidades, precios_cha, strict=False
        ):
            cantidad = _parse_decimal(cantidad_str)
            precio = _parse_decimal(precio_str)
            if not producto_id or cantidad is None or precio is None or cantidad <= 0:
                continue
            lineas_chatarra.append(
                {"producto_id": producto_id, "cantidad": cantidad, "precio": precio}
            )

        if not lineas_catalitico and not lineas_chatarra:
            messages.error(request, "Debes ingresar al menos una línea para guardar la venta.")
            return redirect(_reciclaje_url("ventas/nueva/"))

        errores = []
        for linea in lineas_catalitico:
            catalitico = Catalitico.objects.filter(
                pk=linea["catalitico_id"], empresa=empresa
            ).first()
            if catalitico is None:
                errores.append("Uno de los catalíticos seleccionados no es válido.")
            elif linea["cantidad"] > catalitico.cantidad_stock:
                errores.append(
                    f"Stock insuficiente de {catalitico.codigo}: "
                    f"disponible {catalitico.cantidad_stock}, solicitado {linea['cantidad']}."
                )
        for linea in lineas_chatarra:
            producto = ProductoChatarra.objects.filter(
                pk=linea["producto_id"], empresa=empresa
            ).first()
            if producto is None:
                errores.append("Uno de los productos de chatarra seleccionados no es válido.")
            elif linea["cantidad"] > producto.cantidad_stock:
                errores.append(
                    f"Stock insuficiente de {producto.nombre}: "
                    f"disponible {producto.cantidad_stock}, solicitado {linea['cantidad']}."
                )

        if errores:
            for error in errores:
                messages.error(request, error)
            return redirect(_reciclaje_url("ventas/nueva/"))

        with transaction.atomic():
            venta = VentaReciclaje.objects.create(
                empresa=empresa,
                comprador=comprador,
                creado_por=request.user,
                notas=(request.POST.get("notas") or "").strip(),
            )
            for linea in lineas_catalitico:
                # select_for_update: red de seguridad ante una carrera real entre
                # dos ventas concurrentes del mismo catalítico (caso raro — la
                # validación de arriba ya cubre el camino normal).
                catalitico = Catalitico.objects.select_for_update().get(
                    pk=linea["catalitico_id"], empresa=empresa
                )
                if linea["cantidad"] > catalitico.cantidad_stock:
                    raise ValueError(f"Stock insuficiente de {catalitico.codigo}.")
                nuevo_stock = catalitico.cantidad_stock - linea["cantidad"]
                catalitico.cantidad_stock = nuevo_stock
                if nuevo_stock <= 0:
                    catalitico.estado = Catalitico.ESTADO_VENDIDO
                catalitico.save(update_fields=["cantidad_stock", "estado"])
                DetalleVentaCatalitico.objects.create(
                    venta=venta,
                    catalitico=catalitico,
                    cantidad=linea["cantidad"],
                    precio_unitario=linea["precio"],
                )
            for linea in lineas_chatarra:
                producto = ProductoChatarra.objects.select_for_update().get(
                    pk=linea["producto_id"], empresa=empresa
                )
                if linea["cantidad"] > producto.cantidad_stock:
                    raise ValueError(f"Stock insuficiente de {producto.nombre}.")
                DetalleVentaChatarra.objects.create(
                    venta=venta,
                    producto=producto,
                    cantidad=linea["cantidad"],
                    precio_unitario=linea["precio"],
                )
                ProductoChatarra.objects.filter(pk=producto.pk).update(
                    cantidad_stock=F("cantidad_stock") - linea["cantidad"]
                )

        total_lineas = len(lineas_catalitico) + len(lineas_chatarra)
        messages.success(request, f"Venta #{venta.pk} registrada con {total_lineas} línea(s).")
        return redirect(_reciclaje_url(f"ventas/{venta.pk}/"))

    context = {
        "catalogo_catalitico": Catalitico.objects.filter(
            empresa=empresa,
            estado=Catalitico.ESTADO_DISPONIBLE,
            activo=True,
            cantidad_stock__gt=0,
        ).order_by("codigo"),
        "catalogo_chatarra": ProductoChatarra.objects.filter(
            empresa=empresa, activo=True, cantidad_stock__gt=0
        ).order_by("nombre"),
        "clientes": Cliente.objects.filter(empresa=empresa).order_by("nombre")[:200],
    }
    return render(request, "taller/reciclaje/staff/crear_venta.html", context)


@login_required
@role_required("Owner", "Admin")
def listado_ventas(request):
    empresa = _empresa_o_403(request)
    ventas = (
        VentaReciclaje.objects.filter(empresa=empresa)
        .select_related("comprador")
        .order_by("-created_at")
    )
    page_obj = Paginator(ventas, 20).get_page(request.GET.get("page"))
    return render(request, "taller/reciclaje/staff/listado_ventas.html", {"page_obj": page_obj})


@login_required
@role_required("Owner", "Admin")
def detalle_venta(request, pk):
    empresa = _empresa_o_403(request)
    venta = get_object_or_404(
        VentaReciclaje.objects.select_related("comprador"), pk=pk, empresa=empresa
    )
    context = {
        "venta": venta,
        "detalles_catalitico": venta.detalles_catalitico.select_related("catalitico"),
        "detalles_chatarra": venta.detalles_chatarra.select_related("producto"),
    }
    return render(request, "taller/reciclaje/staff/detalle_venta.html", context)


# ── Stock y reportes ──────────────────────────────────────────────────────────


@login_required
@role_required("Owner", "Admin")
def resumen_stock(request):
    empresa = _empresa_o_403(request)
    context = {
        "catalogo_disponible": Catalitico.objects.filter(
            empresa=empresa, estado=Catalitico.ESTADO_DISPONIBLE, activo=True
        ).order_by("codigo"),
        "chatarra": ProductoChatarra.objects.filter(empresa=empresa, activo=True).order_by(
            "nombre"
        ),
    }
    return render(request, "taller/reciclaje/staff/resumen_stock.html", context)


@login_required
@role_required("Owner", "Admin")
def editar_catalitico(request, pk):
    empresa = _empresa_o_403(request)
    catalitico = get_object_or_404(Catalitico, pk=pk, empresa=empresa)
    if request.method == "POST":
        catalitico.nombre = (request.POST.get("nombre") or catalitico.nombre).strip()
        catalitico.marca_vehiculo = (
            request.POST.get("marca_vehiculo") or catalitico.marca_vehiculo
        ).strip()
        catalitico.modelo_vehiculo = (
            request.POST.get("modelo_vehiculo") or catalitico.modelo_vehiculo
        ).strip()
        precio_venta = _parse_decimal(request.POST.get("precio_venta"))
        if precio_venta is not None:
            catalitico.precio_venta = precio_venta
        catalitico.activo = request.POST.get("activo") == "on"
        catalitico.save()
        messages.success(request, "Catalítico actualizado.")
        return redirect(_reciclaje_url("stock/"))
    return render(
        request, "taller/reciclaje/staff/editar_catalitico.html", {"catalitico": catalitico}
    )


@login_required
@role_required("Owner", "Admin")
def eliminar_catalitico(request, pk):
    empresa = _empresa_o_403(request)
    catalitico = get_object_or_404(Catalitico, pk=pk, empresa=empresa)
    if request.method == "POST":
        tiene_movimientos = (
            catalitico.compras_detalle.exists() or catalitico.ventas_detalle.exists()
        )
        if tiene_movimientos:
            messages.error(
                request, "No se puede eliminar un catalítico con compra o venta registrada."
            )
        else:
            catalitico.delete()
            messages.success(request, "Catalítico eliminado.")
        return redirect(_reciclaje_url("stock/"))
    return render(
        request, "taller/reciclaje/staff/eliminar_catalitico.html", {"catalitico": catalitico}
    )


@login_required
@role_required("Owner", "Admin")
def reporte_fechas(request):
    empresa = _empresa_o_403(request)
    hoy = timezone.now().date()
    fecha_desde = parse_date(request.GET.get("desde") or "") or hoy.replace(day=1)
    fecha_hasta = parse_date(request.GET.get("hasta") or "") or hoy

    compras = CompraReciclaje.objects.filter(
        empresa=empresa, created_at__date__range=[fecha_desde, fecha_hasta]
    ).select_related("cliente")
    ventas = VentaReciclaje.objects.filter(
        empresa=empresa, created_at__date__range=[fecha_desde, fecha_hasta]
    ).select_related("comprador")

    total_compras = sum((c.total() for c in compras), Decimal("0"))
    total_ventas = sum((v.total() for v in ventas), Decimal("0"))

    context = {
        "empresa": empresa,
        "fecha_desde": fecha_desde,
        "fecha_hasta": fecha_hasta,
        "compras": compras,
        "ventas": ventas,
        "total_compras": total_compras,
        "total_ventas": total_ventas,
        "margen": total_ventas - total_compras,
        "fecha_generacion": timezone.now(),
    }

    if request.GET.get("formato") == "pdf":
        from weasyprint import HTML
        from weasyprint.text.fonts import FontConfiguration

        html_string = render_to_string(
            "taller/reciclaje/staff/reporte_fechas_pdf.html", context, request=request
        )
        font_config = FontConfiguration()
        base_url = request.build_absolute_uri("/")
        pdf_bytes = HTML(string=html_string, base_url=base_url).write_pdf(
            font_config=font_config
        )
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="reporte_reciclaje_{fecha_desde}_{fecha_hasta}.pdf"'
        )
        return response

    return render(request, "taller/reciclaje/staff/reporte_fechas.html", context)
