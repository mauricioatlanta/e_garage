"""
CentroOperacionesService — Lógica de datos del Centro de Operaciones.

Encapsula todos los KPIs, rankings, alertas, proyecciones, gráficos y branding
que las vistas del Centro de Operaciones (estándar y espacial) necesitan.
Las vistas son thin wrappers que llaman a build_context() y solo deciden
el template y los flags visuales (es_dashboard_espacial, use_usa_base).
"""

import json
import logging
from calendar import month_abbr
from datetime import date, datetime, timedelta
from decimal import Decimal

from django.conf import settings
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from taller.models.clientes import Cliente
from taller.models.documento import Documento
from taller.models.lineas_documento import LineaRepuesto, LineaServicio
from taller.models.tecnico import Tecnico
from taller.models.vehiculos import Vehiculo

log = logging.getLogger(__name__)

# Expression shared by all subtotal aggregations: precio_unitario × cantidad
_SUBTOTAL_EXPR = ExpressionWrapper(
    F("precio_unitario") * F("cantidad"),
    output_field=DecimalField(max_digits=14, decimal_places=2),
)
_ZERO_DEC = Value(
    Decimal("0.00"),
    output_field=DecimalField(max_digits=14, decimal_places=2),
)


def _sum_subtotal(qs):
    """Aggregate sum of (precio_unitario × cantidad) over a line queryset."""
    return qs.aggregate(total=Coalesce(Sum(_SUBTOTAL_EXPR), _ZERO_DEC))["total"]


class CentroOperacionesService:
    """
    Fuente única de verdad para los datos del Centro de Operaciones.

    Uso desde las vistas:

        context = CentroOperacionesService.build_context(empresa)
        # o con gráficos y branding (dashboard espacial):
        context = CentroOperacionesService.build_context(
            empresa, user=request.user, include_charts=True
        )
    """

    _PAIS_EMOJI = {"CL": "🇨🇱", "US": "🇺🇸", "MX": "🇲🇽"}

    @classmethod
    def build_context(cls, empresa, user=None, hoy=None, include_charts=False):
        """
        Construye el contexto completo para el Centro de Operaciones.

        Args:
            empresa: instancia de Empresa (tenant).
            user: request.user; requerido solo si include_charts=True (para branding).
            hoy: date de referencia; si None usa date.today() (inyectable en tests).
            include_charts: si True, computa chart_data_json y BRAND (14 queries extra).

        Returns:
            dict listo para pasar a render(). No incluye flags de template
            (es_dashboard_espacial, use_usa_base) — los decide la vista.
        """
        if hoy is None:
            hoy = date.today()

        hace_7_dias = hoy - timedelta(days=7)
        hace_30_dias = hoy - timedelta(days=30)
        inicio_mes = date(hoy.year, hoy.month, 1)
        inicio_mes_dt = cls._inicio_mes_aware(hoy)

        kpis_docs = cls._kpis_documentos(empresa, hoy, hace_7_dias, inicio_mes)
        kpis_fac = cls._kpis_facturacion(empresa, hoy, hace_7_dias, inicio_mes)
        kpis_cli = cls._kpis_clientes(empresa, inicio_mes_dt, hace_7_dias)
        tecnicos_activos = cls._tecnicos_activos(empresa)
        servicios_top = cls._servicios_top(empresa, hace_30_dias)
        tecnicos_productivos = cls._tecnicos_productivos(empresa, hace_30_dias)
        kpis_estado = cls._kpis_estado_documentos(empresa, inicio_mes)
        kpis_veh = cls._kpis_vehiculos(empresa)
        alertas_data = cls._alertas(empresa, hoy)
        ticket_promedio = cls._ticket_promedio(empresa, inicio_mes, kpis_estado["facturas_mes"])
        eficiencia = cls._eficiencia_conversion(
            kpis_estado["facturas_mes"], kpis_estado["presupuestos_mes"]
        )
        proyecciones = cls._proyecciones(
            hoy, inicio_mes,
            kpis_docs["documentos_mes"],
            kpis_fac["facturacion_mes_total"],
        )
        checklist = cls._checklist_onboarding(
            empresa,
            tecnicos_activos,
            kpis_cli["clientes_activos"],
            kpis_veh["vehiculos_registrados"],
            kpis_docs["total_documentos"],
        )

        context = {
            "empresa": empresa,
            "pais_emoji": cls._PAIS_EMOJI.get(empresa.pais, "🌎"),
            "moneda": empresa.simbolo_moneda,
            **kpis_docs,
            **kpis_fac,
            **kpis_cli,
            "tecnicos_activos": tecnicos_activos,
            "servicios_top": servicios_top,
            "tecnicos_productivos": tecnicos_productivos,
            **kpis_estado,
            **kpis_veh,
            "alertas": alertas_data["alertas"],
            "clientes_inactivos": alertas_data["clientes_inactivos"],
            **proyecciones,
            "ticket_promedio": ticket_promedio,
            "eficiencia_conversion": eficiencia,
            "checklist_onboarding": checklist,
            "checklist_completo": all(checklist.values()),
            "fecha_hoy": hoy,
            "mes_actual": hoy.strftime("%B %Y"),
            # Defaults; populated below when include_charts=True
            "chart_data_json": "{}",
            "BRAND": {},
            "company_name": "",
            "company_logo_url": "",
            "company_color": "",
            "company_tagline": "",
        }

        if include_charts:
            context["chart_data_json"] = cls._chart_data_json(
                empresa, hoy, servicios_top, tecnicos_productivos
            )
            if user is not None:
                from taller.services.branding_service import BrandingService
                brand = BrandingService.get_brand(empresa, user=user)
                brand_dict = brand.as_dict()
                context.update({
                    "BRAND": brand_dict,
                    "company_name": brand_dict.get("name", ""),
                    "company_logo_url": brand_dict.get("logo_url", ""),
                    "company_color": brand_dict.get("primary_color", ""),
                    "company_tagline": brand_dict.get("tagline", ""),
                })

        return context

    # ------------------------------------------------------------------
    # Private query methods — each returns a flat dict or scalar
    # ------------------------------------------------------------------

    @classmethod
    def _inicio_mes_aware(cls, hoy):
        inicio = datetime(hoy.year, hoy.month, 1, 0, 0, 0)
        if settings.USE_TZ:
            return timezone.make_aware(inicio, timezone.get_current_timezone())
        return inicio

    @classmethod
    def _kpis_documentos(cls, empresa, hoy, hace_7_dias, inicio_mes):
        qs = Documento.objects.filter(empresa=empresa)
        return {
            "documentos_hoy": qs.filter(fecha_emision=hoy).count(),
            "documentos_semana": qs.filter(fecha_emision__gte=hace_7_dias).count(),
            "documentos_mes": qs.filter(fecha_emision__gte=inicio_mes).count(),
            "total_documentos": qs.count(),
        }

    @classmethod
    def _kpis_facturacion(cls, empresa, hoy, hace_7_dias, inicio_mes):
        base_hoy = LineaServicio.objects.filter(
            documento__empresa=empresa, documento__fecha_emision=hoy, documento__tipo="FAC"
        )
        base_sem = LineaServicio.objects.filter(
            documento__empresa=empresa,
            documento__fecha_emision__gte=hace_7_dias,
            documento__tipo="FAC",
        )
        base_mes_srv = LineaServicio.objects.filter(
            documento__empresa=empresa,
            documento__fecha_emision__gte=inicio_mes,
            documento__tipo="FAC",
        )
        base_mes_rep = LineaRepuesto.objects.filter(
            documento__empresa=empresa,
            documento__fecha_emision__gte=inicio_mes,
            documento__tipo="FAC",
        )

        facturacion_servicios_mes = _sum_subtotal(base_mes_srv)
        total_repuestos_mes = _sum_subtotal(base_mes_rep) or Decimal("0.00")

        iva_repuestos = Decimal("0.00")
        if empresa.pais == "CL":
            iva_repuestos = (total_repuestos_mes * Decimal("0.19")).quantize(Decimal("0.01"))

        return {
            "facturacion_servicios_hoy": _sum_subtotal(base_hoy),
            "facturacion_servicios_semana": _sum_subtotal(base_sem),
            "facturacion_servicios_mes": facturacion_servicios_mes,
            "total_repuestos_mes": total_repuestos_mes,
            "iva_repuestos": iva_repuestos,
            "facturacion_mes_total": (facturacion_servicios_mes or Decimal("0"))
                + (total_repuestos_mes or Decimal("0")),
        }

    @classmethod
    def _kpis_clientes(cls, empresa, inicio_mes_dt, hace_7_dias):
        now = timezone.now()
        clientes_atendidos = (
            Documento.objects.filter(empresa=empresa, fecha_emision__gte=hace_7_dias)
            .values("cliente")
            .distinct()
            .count()
        )
        return {
            "clientes_activos": Cliente.objects.filter(empresa=empresa).count(),
            "clientes_nuevos_mes": Cliente.objects.filter(
                empresa=empresa,
                created_at__gte=inicio_mes_dt,
                created_at__lte=now,
            ).count(),
            "clientes_atendidos_semana": clientes_atendidos,
        }

    @classmethod
    def _tecnicos_activos(cls, empresa):
        return Tecnico.objects.filter(empresa=empresa, activo=True).count()

    @classmethod
    def _servicios_top(cls, empresa, hace_30_dias, top=5):
        return list(
            LineaServicio.objects.filter(
                documento__empresa=empresa, documento__fecha_emision__gte=hace_30_dias
            )
            .values("nombre")
            .annotate(cantidad=Count("id"))
            .order_by("-cantidad")[:top]
        )

    @classmethod
    def _tecnicos_productivos(cls, empresa, hace_30_dias, top=5):
        tecnico_efectivo = Coalesce(F("tecnico_responsable"), F("documento__tecnico_responsable"))
        lineas = LineaServicio.objects.filter(
            documento__empresa=empresa,
            documento__fecha_emision__gte=hace_30_dias,
            documento__tipo="FAC",
        ).exclude(
            Q(tecnico_responsable__isnull=True) & Q(documento__tecnico_responsable__isnull=True)
        )

        raw = list(
            lineas.annotate(
                tecnico_id=tecnico_efectivo,
                ingresos_generados=Coalesce(Sum(_SUBTOTAL_EXPR), _ZERO_DEC),
                docs_realizados=Count("documento", distinct=True),
            )
            .values("tecnico_id", "ingresos_generados", "docs_realizados")
            .exclude(tecnico_id__isnull=True)
            .order_by("-ingresos_generados")[:top]
        )

        tecnicos_ids = [row["tecnico_id"] for row in raw]
        tecnicos_map = {
            t.id: t
            for t in Tecnico.objects.filter(id__in=tecnicos_ids).only("id", "nombre", "activo")
        }

        return [
            {
                "tecnico": tecnicos_map.get(row["tecnico_id"]),
                "ingresos_generados": row["ingresos_generados"],
                "docs_realizados": row["docs_realizados"],
            }
            for row in raw
        ]

    @classmethod
    def _kpis_estado_documentos(cls, empresa, inicio_mes):
        qs = Documento.objects.filter(empresa=empresa)
        return {
            "presupuestos_pendientes": qs.filter(tipo="PRES").count(),
            "ordenes_en_proceso": qs.filter(tipo="OT").count(),
            "presupuestos_mes": qs.filter(tipo="PRES", fecha_emision__gte=inicio_mes).count(),
            "facturas_mes": qs.filter(tipo="FAC", fecha_emision__gte=inicio_mes).count(),
        }

    @classmethod
    def _kpis_vehiculos(cls, empresa):
        return {
            "vehiculos_registrados": Vehiculo.objects.filter(empresa=empresa).count(),
            "marcas_atendidas": (
                Vehiculo.objects.filter(empresa=empresa)
                .values("marca__nombre")
                .distinct()
                .count()
            ),
        }

    @classmethod
    def _alertas(cls, empresa, hoy):
        alertas = []

        clientes_inactivos = (
            Cliente.objects.filter(empresa=empresa, documentos__isnull=False)
            .exclude(documentos__fecha_emision__gte=hoy - timedelta(days=60))
            .distinct()
            .count()
        )
        if clientes_inactivos > 0:
            alertas.append({
                "tipo": "warning",
                "titulo": f"{clientes_inactivos} clientes inactivos",
                "descripcion": "No han visitado el taller en los últimos 60 días",
                "accion": "Enviar promoción de mantenimiento",
            })

        presupuestos_antiguos = Documento.objects.filter(
            empresa=empresa, tipo="PRES", fecha_emision__lt=hoy - timedelta(days=15)
        ).count()
        if presupuestos_antiguos > 0:
            alertas.append({
                "tipo": "info",
                "titulo": f"{presupuestos_antiguos} presupuestos antiguos",
                "descripcion": "Presupuestos de más de 15 días sin convertir",
                "accion": "Contactar clientes para seguimiento",
            })

        return {"alertas": alertas, "clientes_inactivos": clientes_inactivos}

    @classmethod
    def _ticket_promedio(cls, empresa, inicio_mes, facturas_mes):
        srv = LineaServicio.objects.filter(
            documento__empresa=empresa, documento__tipo="FAC",
            documento__fecha_emision__gte=inicio_mes,
        )
        rep = LineaRepuesto.objects.filter(
            documento__empresa=empresa, documento__tipo="FAC",
            documento__fecha_emision__gte=inicio_mes,
        )
        monto = (
            Coalesce(srv.aggregate(t=Sum(_SUBTOTAL_EXPR))["t"], Decimal("0"))
            + Coalesce(rep.aggregate(t=Sum(_SUBTOTAL_EXPR))["t"], Decimal("0"))
        )
        return (monto / facturas_mes) if facturas_mes else Decimal("0")

    @classmethod
    def _proyecciones(cls, hoy, inicio_mes, documentos_mes, facturacion_mes_total):
        if documentos_mes > 0:
            dias = (hoy - inicio_mes).days + 1
            return {
                "proyeccion_docs_mes": int((documentos_mes / dias) * 30),
                "proyeccion_facturacion": (
                    (facturacion_mes_total / dias) * 30
                    if facturacion_mes_total > 0
                    else 0
                ),
            }
        return {"proyeccion_docs_mes": 0, "proyeccion_facturacion": 0}

    @classmethod
    def _eficiencia_conversion(cls, facturas_mes, presupuestos_mes):
        return (facturas_mes / max(presupuestos_mes + facturas_mes, 1)) * 100

    @classmethod
    def _checklist_onboarding(
        cls, empresa, tecnicos_activos, clientes_activos, vehiculos_registrados, total_documentos
    ):
        return {
            "empresa_configurada": bool(
                empresa.nombre_taller
                and empresa.pais
                and empresa.moneda
                and hasattr(empresa, "config")
                and empresa.config.tasa_impuesto is not None
            ),
            "tecnico_creado": tecnicos_activos > 0,
            "cliente_creado": clientes_activos > 0,
            "vehiculo_creado": vehiculos_registrados > 0,
            "documento_creado": total_documentos > 0,
        }

    @classmethod
    def _chart_data_json(cls, empresa, hoy, servicios_top, tecnicos_productivos):
        """
        Construye los tres datasets de gráficos como JSON para Chart.js.

        Ingresos mensuales: 7 queries × 2 modelos (LineaServicio + LineaRepuesto)
        por mes = 14 queries en total. Candidato a optimización con TruncMonth
        en una versión futura, pero se mantiene la lógica original.
        """
        # 1. Ingresos mensuales (últimos 7 meses)
        labels_ingresos = []
        data_ingresos = []
        for i in range(6, -1, -1):
            mes_actual = hoy.month
            año_actual = hoy.year
            if mes_actual > i:
                mes_t = mes_actual - i
                año_t = año_actual
            else:
                restantes = i - mes_actual
                mes_t = 12 - (restantes % 12) or 12
                año_t = año_actual - (1 + restantes // 12)

            inicio = date(año_t, mes_t, 1)
            fin = date(año_t + 1, 1, 1) if mes_t == 12 else date(año_t, mes_t + 1, 1)

            srv = _sum_subtotal(
                LineaServicio.objects.filter(
                    documento__empresa=empresa, documento__tipo="FAC",
                    documento__fecha_emision__gte=inicio,
                    documento__fecha_emision__lt=fin,
                )
            ) or Decimal("0")
            rep = _sum_subtotal(
                LineaRepuesto.objects.filter(
                    documento__empresa=empresa, documento__tipo="FAC",
                    documento__fecha_emision__gte=inicio,
                    documento__fecha_emision__lt=fin,
                )
            ) or Decimal("0")

            labels_ingresos.append(month_abbr[inicio.month].upper())
            data_ingresos.append(float(srv + rep))

        # 2. Distribución porcentual de servicios top
        labels_srv = []
        data_srv = []
        if servicios_top:
            total_count = sum(s["cantidad"] for s in servicios_top)
            for s in servicios_top[:5]:
                labels_srv.append(s["nombre"][:20])
                pct = (s["cantidad"] / total_count * 100) if total_count > 0 else 0
                data_srv.append(round(pct, 1))

        # 3. Técnicos: porcentaje relativo al máximo
        labels_tec = []
        data_tec = []
        if tecnicos_productivos:
            max_ing = max(float(t["ingresos_generados"] or 0) for t in tecnicos_productivos)
            for t in tecnicos_productivos[:4]:
                nombre = t["tecnico"].nombre if t["tecnico"] else "Unknown"
                labels_tec.append(nombre[:15])
                ing = float(t["ingresos_generados"] or 0)
                data_tec.append(round((ing / max_ing * 100) if max_ing > 0 else 0, 1))

        return json.dumps({
            "ingresos_mensuales": {"labels": labels_ingresos, "data": data_ingresos},
            "servicios": {"labels": labels_srv, "data": data_srv},
            "tecnicos": {"labels": labels_tec, "data": data_tec},
        })
