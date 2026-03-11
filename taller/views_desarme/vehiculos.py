"""
Vistas de vehículos de desarme: listado Kanban y creación rápida.
"""

from decimal import Decimal
from collections import OrderedDict

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import (
    DecimalField,
    ExpressionWrapper,
    F,
    OuterRef,
    Q,
    Subquery,
    Sum,
    Value,
)
from django.db.models.functions import Coalesce
from django.shortcuts import redirect, render

from taller.models import CostoVehiculoDesarme, LineaRepuesto, Vehiculo
from taller.utils.empresa import get_or_create_empresa
from taller.utils.url_helpers import reverse_country
from taller.vehiculos.forms import VehiculoForm

# Orden de columnas del tablero Kanban por estado
ESTADOS_KANBAN = [
    ("ingresado", "Ingresado"),
    ("en_desarme", "En desarme"),
    ("con_piezas", "Con piezas disponibles"),
    ("agotado", "Agotado"),
    ("cerrado", "Cerrado"),
]


def _normalizar_estado(estado):
    """Trata estado vacío o desconocido como 'ingresado' (explícito y seguro)."""
    s = (estado or "").strip()
    if s in ("ingresado", "en_desarme", "con_piezas", "agotado", "cerrado"):
        return s
    return "ingresado"


def _annotate_metricas_financieras(queryset):
    """
    Anota costo_total_desarme, ingresos_repuestos_total y utilidad_total a nivel queryset
    para evitar N+1 en el Kanban. Cada tarjeta recibe los valores listos para render.
    """
    # Costo base = suma de campos del vehículo
    costo_base = (
        Coalesce(F("precio_compra"), Value(Decimal("0")))
        + Coalesce(F("costo_transporte"), Value(Decimal("0")))
        + Coalesce(F("costo_grua"), Value(Decimal("0")))
        + Coalesce(F("costo_papeles"), Value(Decimal("0")))
        + Coalesce(F("otros_costos_base"), Value(Decimal("0")))
    )

    decimal_field = DecimalField(max_digits=14, decimal_places=2)

    # Costos adicionales (CostoVehiculoDesarme)
    costos_adicionales_sub = (
        CostoVehiculoDesarme.objects.filter(vehiculo_id=OuterRef("pk"))
        .values("vehiculo")
        .annotate(total=Sum("monto"))
        .values("total")
    )

    # Ingresos por repuestos vendidos. documento__estado="EMITIDO" = canónico de vendido/facturado.
    # LineaRepuesto.descuento es porcentaje 0–100 (help_text del modelo).
    linea_subtotal = ExpressionWrapper(
        F("cantidad") * F("precio_unitario") * (1 - Coalesce(F("descuento"), Value(0)) / 100),
        output_field=decimal_field,
    )
    ingresos_sub = (
        LineaRepuesto.objects.filter(
            repuesto__vehiculo_origen_id=OuterRef("pk"),
            documento__estado="EMITIDO",
        )
        .values("repuesto__vehiculo_origen")
        .annotate(total=Sum(linea_subtotal))
        .values("total")
    )

    # output_field explícito evita errores raros entre SQLite/PostgreSQL al mezclar tipos
    subquery_costos = Subquery(costos_adicionales_sub, output_field=decimal_field)
    subquery_ingresos = Subquery(ingresos_sub, output_field=decimal_field)

    # Usamos nombres distintos a las propiedades del modelo para que el template
    # reciba valores precomputados sin disparar N+1
    return (
        queryset.annotate(
            _costos_adicionales=Coalesce(subquery_costos, Value(Decimal("0"))),
            _ingresos_repuestos=Coalesce(subquery_ingresos, Value(Decimal("0"))),
        )
        .annotate(
            kanban_costo_total=costo_base + F("_costos_adicionales"),
            kanban_ingresos_total=F("_ingresos_repuestos"),
        )
        .annotate(
            # utilidad = ingresos_totales - costo; ingresos_totales = ingresos_repuestos + chatarra
            kanban_utilidad_total=(
                F("kanban_ingresos_total")
                + Coalesce(F("ingreso_final_chatarra"), Value(Decimal("0")))
                - F("kanban_costo_total")
            ),
        )
    )


@login_required
def lista_vehiculos_desarme(request):
    """
    Tablero Kanban de vehículos de desarme (tipo_uso='desarme') para la empresa activa.
    Columnas por estado: ingresado, en_desarme, con_piezas, agotado, cerrado.
    Permite búsqueda por patente, VIN, marca y modelo.

    Métricas financieras anotadas a nivel queryset (evita N+1).
    Orden en columnas: más recientes primero (fecha_ingreso_desarme desc, id desc).
    """
    empresa = get_or_create_empresa(request)

    qs = (
        Vehiculo.objects.filter(empresa=empresa, tipo_uso="desarme")
        .select_related("marca", "modelo", "cliente")
        .order_by("-fecha_ingreso_desarme", "-id")
    )
    qs = _annotate_metricas_financieras(qs)

    q = (request.GET.get("q") or "").strip()
    if q:
        qs = qs.filter(
            Q(patente__icontains=q)
            | Q(vin__icontains=q)
            | Q(marca_texto__icontains=q)
            | Q(modelo_texto__icontains=q)
            | Q(marca__nombre__icontains=q)
            | Q(modelo__nombre__icontains=q)
        )

    # Agrupar por estado para el Kanban. El orden dentro de cada columna se preserva
    # del queryset (-fecha_ingreso_desarme, -id): más recientes primero.
    vehiculos_por_estado = OrderedDict((k, []) for k, _ in ESTADOS_KANBAN)
    for v in qs:
        estado = _normalizar_estado(v.estado_desarme)
        vehiculos_por_estado.setdefault(estado, []).append(v)

    totales_por_estado = {k: len(vehiculos_por_estado.get(k, [])) for k, _ in ESTADOS_KANBAN}
    total_vehiculos = sum(totales_por_estado.values())

    # Estructura para template: list of (estado_key, estado_label, vehiculos)
    columnas_kanban = [
        (estado_key, estado_label, vehiculos_por_estado.get(estado_key, []))
        for estado_key, estado_label in ESTADOS_KANBAN
    ]

    context = {
        "vehiculos": qs,
        "columnas_kanban": columnas_kanban,
        "estados_kanban": ESTADOS_KANBAN,
        "totales_por_estado": totales_por_estado,
        "total_vehiculos": total_vehiculos,
        "q": q,
    }
    return render(request, "taller/desarme/vehiculos_list.html", context)


@login_required
def crear_vehiculo_desarme(request):
    """
    Crear vehículo preconfigurado como tipo_uso='desarme'.

    Reutiliza VehiculoForm y la plantilla común de vehículos,
    pero fuerza tipo_uso='desarme' y empresa obtenida con get_or_create_empresa.
    """
    empresa = get_or_create_empresa(request)

    if request.method == "POST":
        data = request.POST.copy()
        data["tipo_uso"] = "desarme"
        form = VehiculoForm(data, user=request.user, request=request)
        if form.is_valid():
            vehiculo = form.save(commit=False)
            vehiculo.empresa = empresa
            vehiculo.tipo_uso = "desarme"
            vehiculo.save()
            form.save_m2m()
            messages.success(
                request,
                "Vehículo de desarme creado correctamente. Ahora puedes inspeccionar sus piezas.",
            )
            mapa_url = reverse_country(
                request,
                "desarme:mapa_piezas",
                kwargs={"pk": vehiculo.pk},
            )
            return redirect(mapa_url)
    else:
        initial = {"tipo_uso": "desarme"}
        form = VehiculoForm(user=request.user, request=request, initial=initial)

    context = {
        "form": form,
        "is_desarme_create": True,
    }
    return render(request, "taller/common/vehiculos/vehiculo_form.html", context)
