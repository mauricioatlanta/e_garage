"""Mini-POS exclusivo del módulo Desarme — venta simplificada de repuestos."""

import logging
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from taller.models.pieza_desarme import PiezaDesarme, ESTADO_DISPONIBLE, ESTADO_VENDIDA
from taller.models.venta_desarme import VentaDesarme, LineaVentaDesarme
from taller.models.vendedor_desarme import VendedorDesarme

log = logging.getLogger(__name__)

SESSION_KEY = "desarme_venta_rapida"


def _empresa(request):
    return getattr(request.user, "empresa", None)


def _url(request, suffix):
    path = request.path
    if "/us/" in path:
        base = "/us/en/desarme/"
    else:
        base = "/cl/es/desarme/"
    return base + suffix.lstrip("/")


# ── Paso 1: recibir carrito y guardar en sesión ───────────────────────────────

@login_required
@require_POST
def iniciar_venta_rapida(request):
    """Recibe el carrito (pieza_ids + cantidades), valida y guarda en sesión."""
    empresa = _empresa(request)
    if not empresa:
        return redirect("/")

    pieza_ids = request.POST.getlist("pieza_ids")
    if not pieza_ids:
        messages.warning(request, "Agrega al menos un repuesto al carrito.")
        return redirect(_url(request, "piezas/"))

    piezas_qs = PiezaDesarme.objects.filter(
        pk__in=pieza_ids,
        empresa=empresa,
        activo=True,
        estado_pieza=ESTADO_DISPONIBLE,
        cantidad__gt=0,
    )
    piezas_by_id = {p.pk: p for p in piezas_qs}

    items = []
    for raw_id in pieza_ids:
        try:
            pid = int(raw_id)
        except (ValueError, TypeError):
            continue
        pieza = piezas_by_id.get(pid)
        if not pieza:
            continue
        try:
            cant = int(request.POST.get(f"cantidad_{pid}", "1") or 1)
        except (ValueError, TypeError):
            cant = 1
        cant = max(1, min(cant, pieza.cantidad))
        precio = float(pieza.precio_venta_sugerido or 0)
        items.append({
            "id": pid,
            "nombre": pieza.nombre,
            "codigo": pieza.codigo or "",
            "cantidad": cant,
            "precio": precio,
            "subtotal": round(precio * cant, 2),
        })

    if not items:
        messages.warning(request, "Ningún repuesto seleccionado está disponible.")
        return redirect(_url(request, "piezas/"))

    request.session[SESSION_KEY] = items
    return redirect(_url(request, "ventas/nueva/"))


# ── Paso 2: confirmación ──────────────────────────────────────────────────────

@login_required
def confirmar_venta_rapida(request):
    """Muestra el formulario de confirmación y crea la venta al submitir."""
    empresa = _empresa(request)
    if not empresa:
        return redirect("/")

    items = request.session.get(SESSION_KEY)
    if not items:
        messages.warning(request, "No hay repuestos seleccionados. Vuelve a la lista.")
        return redirect(_url(request, "piezas/"))

    total = sum(i["subtotal"] for i in items)
    vendedores = VendedorDesarme.objects.filter(empresa=empresa, activo=True).order_by("nombre")

    if request.method == "POST":
        cliente_nombre = request.POST.get("cliente_nombre", "").strip()
        vendedor_id = request.POST.get("vendedor", "").strip()
        notas = request.POST.get("notas", "").strip()

        vendedor = None
        if vendedor_id:
            vendedor = VendedorDesarme.objects.filter(pk=vendedor_id, empresa=empresa).first()

        try:
            with transaction.atomic():
                # Bloquear piezas y re-validar disponibilidad
                pieza_ids = [i["id"] for i in items]
                piezas_locked = {
                    p.pk: p
                    for p in PiezaDesarme.objects.select_for_update().filter(
                        pk__in=pieza_ids, empresa=empresa
                    )
                }

                errores = []
                for item in items:
                    p = piezas_locked.get(item["id"])
                    if not p or p.estado_pieza != ESTADO_DISPONIBLE:
                        errores.append(f"'{item['nombre']}' ya no está disponible.")
                    elif p.cantidad < item["cantidad"]:
                        errores.append(
                            f"'{item['nombre']}': stock insuficiente "
                            f"(disponible: {p.cantidad}, solicitado: {item['cantidad']})."
                        )
                if errores:
                    for e in errores:
                        messages.error(request, e)
                    raise ValueError("stock")

                venta = VentaDesarme(
                    empresa=empresa,
                    cliente_nombre=cliente_nombre,
                    vendedor=vendedor,
                    notas=notas,
                    total=Decimal(str(total)),
                )
                venta.save()

                for item in items:
                    pieza = piezas_locked[item["id"]]
                    LineaVentaDesarme.objects.create(
                        venta=venta,
                        pieza=pieza,
                        nombre_pieza=item["nombre"],
                        codigo_pieza=item["codigo"],
                        cantidad=item["cantidad"],
                        precio_unitario=Decimal(str(item["precio"])),
                        subtotal=Decimal(str(item["subtotal"])),
                    )
                    pieza.cantidad -= item["cantidad"]
                    if pieza.cantidad <= 0:
                        pieza.cantidad = 0
                        pieza.estado_pieza = ESTADO_VENDIDA
                        pieza.activo = False
                    pieza.save(update_fields=["cantidad", "estado_pieza", "activo"])

        except ValueError:
            pass  # errores ya agregados a messages
        except Exception as e:
            log.exception("Error creando venta rápida de desarme")
            messages.error(request, f"Error al procesar la venta: {e}")
        else:
            del request.session[SESSION_KEY]
            messages.success(request, f"✅ Venta #{venta.numero} registrada.")
            return redirect(_url(request, f"ventas/{venta.pk}/recibo/"))

    return render(request, "taller/desarme/ventas/confirmar.html", {
        "items": items,
        "total": total,
        "vendedores": vendedores,
    })


# ── Recibo ────────────────────────────────────────────────────────────────────

@login_required
def recibo_venta(request, pk):
    empresa = _empresa(request)
    if not empresa:
        return redirect("/")
    venta = get_object_or_404(VentaDesarme, pk=pk, empresa=empresa)
    return render(request, "taller/desarme/ventas/recibo.html", {"venta": venta})


# ── Historial de ventas ───────────────────────────────────────────────────────

@login_required
def lista_ventas(request):
    empresa = _empresa(request)
    if not empresa:
        return redirect("/")
    ventas = VentaDesarme.objects.filter(empresa=empresa).prefetch_related("lineas")
    return render(request, "taller/desarme/ventas/lista.html", {"ventas": ventas})


# ── Anular venta ─────────────────────────────────────────────────────────────

@login_required
@require_POST
def anular_venta(request, pk):
    empresa = _empresa(request)
    if not empresa:
        return redirect("/")
    venta = get_object_or_404(VentaDesarme, pk=pk, empresa=empresa)

    if venta.estado == "ANULADA":
        messages.warning(request, "Esta venta ya estaba anulada.")
        return redirect(_url(request, f"ventas/{pk}/recibo/"))

    with transaction.atomic():
        for linea in venta.lineas.select_related("pieza"):
            pieza = linea.pieza
            if pieza:
                pieza.cantidad = (pieza.cantidad or 0) + linea.cantidad
                pieza.estado_pieza = ESTADO_DISPONIBLE
                pieza.activo = True
                pieza.save(update_fields=["cantidad", "estado_pieza", "activo"])
        venta.estado = "ANULADA"
        venta.save(update_fields=["estado"])

    messages.success(request, f"Venta #{venta.numero} anulada. Stock repuesto.")
    return redirect(_url(request, f"ventas/{pk}/recibo/"))
