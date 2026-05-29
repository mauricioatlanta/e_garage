"""
Servicio de Dashboard de Inteligencia de Negocios (BI)

Maneja agregaciones multi-tenant eficientes usando el ORM de Django.
Todas las consultas se ejecutan en la base de datos para evitar loops en Python.
"""

import logging
from datetime import timedelta
from decimal import Decimal

from django.core.cache import cache
from django.db.models import Count, Q, Sum
from django.db.models.functions import Coalesce, TruncMonth
from django.utils import timezone

from taller.models.documento import Documento

log = logging.getLogger(__name__)


class DashboardService:
    """
    Servicio dedicado para dashboard de BI con agregaciones eficientes.

    Features:
    - Agregaciones en DB (no loops en Python)
    - Multi-tenant seguro
    - Caching para optimización
    - KPIs principales del mes
    - Gráficos de tendencias
    - Rankings de técnicos
    """

    def __init__(self, empresa, cache_enabled=True, cache_timeout=3600):
        """
        Inicializa el servicio de dashboard.

        Args:
            empresa: Instancia de Empresa (multi-tenant)
            cache_enabled: Habilitar cache (default: True)
            cache_timeout: Tiempo de cache en segundos (default: 1 hora)
        """
        self.empresa = empresa
        self.cache_enabled = cache_enabled
        self.cache_timeout = cache_timeout

        # Definir rango "Este Mes"
        now = timezone.now()
        self.inicio_mes = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        self.fin_mes = (self.inicio_mes + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)

        # Cache key base
        self.cache_key_base = f"dashboard_{empresa.id}"

    def _get_cache_key(self, suffix):
        """Genera clave de cache"""
        return f"{self.cache_key_base}_{suffix}"

    def get_kpis_principales(self, force_refresh=False):
        """
        Retorna tarjetas de KPIs principales para el mes actual.

        Returns:
            dict: {
                'total_ventas': Decimal,
                'total_ot': int,
                'total_facturas': int,
                'total_presupuestos': int,
                'ticket_promedio': Decimal,
                'tasa_conversion': float,  # Presupuestos -> Facturas
            }
        """
        cache_key = self._get_cache_key("kpis_mes")

        # Intentar obtener de cache
        if self.cache_enabled and not force_refresh:
            cached = cache.get(cache_key)
            if cached is not None:
                log.debug(
                    f"[DashboardService] KPIs obtenidos de cache para empresa {self.empresa.id}"
                )
                return cached

        # Query base: documentos emitidos del mes actual
        qs_mes = Documento.objects.filter(
            empresa=self.empresa,
            fecha_emision__range=(self.inicio_mes, self.fin_mes),
            estado="EMITIDO",
        )

        # Agregación en una sola consulta DB (eficiente)
        stats = qs_mes.aggregate(
            total_ventas=Coalesce(Sum("total"), Decimal("0.00")),
            total_ot=Count("id", filter=Q(tipo="OT")),
            total_facturas=Count("id", filter=Q(tipo="FAC")),
            total_presupuestos=Count("id", filter=Q(tipo="PRES")),
            total_documentos=Count("id"),
        )

        # Calcular ticket promedio (evitar división por cero)
        total_docs = stats["total_documentos"] or 1
        ticket_promedio = stats["total_ventas"] / Decimal(str(total_docs))

        # Calcular tasa de conversión (Presupuestos -> Facturas)
        # Presupuestos del mes anterior (asumiendo que se convierten al mes siguiente)
        hace_2_meses = (self.inicio_mes - timedelta(days=32)).replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        inicio_mes_anterior = (self.inicio_mes - timedelta(days=1)).replace(
            hour=23, minute=59, second=59, microsecond=999999
        )

        presupuestos_mes_anterior = Documento.objects.filter(
            empresa=self.empresa,
            fecha_emision__range=(hace_2_meses, inicio_mes_anterior),
            tipo="PRES",
            estado="EMITIDO",
        ).count()

        # Facturas del mes actual (convertidas de presupuestos)
        # Simplificación: tasa = facturas / (presupuestos_mes_anterior + 1)
        tasa_conversion = 0.0
        if presupuestos_mes_anterior > 0:
            tasa_conversion = (stats["total_facturas"] / presupuestos_mes_anterior) * 100
        elif stats["total_facturas"] > 0:
            tasa_conversion = 100.0

        # Construir resultado
        result = {
            "total_ventas": stats["total_ventas"],
            "total_ot": stats["total_ot"],
            "total_facturas": stats["total_facturas"],
            "total_presupuestos": stats["total_presupuestos"],
            "ticket_promedio": ticket_promedio,
            "tasa_conversion": round(tasa_conversion, 2),
        }

        # Guardar en cache
        if self.cache_enabled:
            cache.set(cache_key, result, self.cache_timeout)
            log.debug(f"[DashboardService] KPIs guardados en cache para empresa {self.empresa.id}")

        return result

    def get_ventas_anuales_chart(self, meses=12, force_refresh=False):
        """
        Retorna datos para el gráfico de líneas (Últimos N meses).

        Args:
            meses: Número de meses a mostrar (default: 12)
            force_refresh: Forzar refresco (ignorar cache)

        Returns:
            dict: {
                'labels': list[str],  # ['Ene 2024', 'Feb 2024', ...]
                'data': list[float],  # [50000.0, 75000.0, ...]
            }
        """
        cache_key = self._get_cache_key(f"ventas_anuales_{meses}")

        # Intentar obtener de cache
        if self.cache_enabled and not force_refresh:
            cached = cache.get(cache_key)
            if cached is not None:
                log.debug(
                    f"[DashboardService] Gráfico obtenido de cache para empresa {self.empresa.id}"
                )
                return cached

        # Calcular fecha de inicio (N meses atrás)
        now = timezone.now()
        inicio_consulta = (now - timedelta(days=meses * 30)).replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )

        # Agrupar por mes usando TruncMonth (eficiente en DB)
        datos = (
            Documento.objects.filter(
                empresa=self.empresa, estado="EMITIDO", fecha_emision__gte=inicio_consulta
            )
            .annotate(mes=TruncMonth("fecha_emision"))
            .values("mes")
            .annotate(total=Coalesce(Sum("total"), Decimal("0.00")))
            .order_by("mes")
        )

        # Formatear para Chart.js
        labels = []
        values = []

        for d in datos:
            # Formato de fecha: "Ene 2024" (en español)
            mes_str = d["mes"].strftime("%b %Y")
            # Traducir mes al español si es necesario
            meses_es = {
                "Jan": "Ene",
                "Feb": "Feb",
                "Mar": "Mar",
                "Apr": "Abr",
                "May": "May",
                "Jun": "Jun",
                "Jul": "Jul",
                "Aug": "Ago",
                "Sep": "Sep",
                "Oct": "Oct",
                "Nov": "Nov",
                "Dec": "Dic",
            }
            for en, es in meses_es.items():
                mes_str = mes_str.replace(en, es)

            labels.append(mes_str)
            values.append(float(d["total"]))

        result = {
            "labels": labels,
            "data": values,
        }

        # Guardar en cache
        if self.cache_enabled:
            cache.set(cache_key, result, self.cache_timeout)
            log.debug(
                f"[DashboardService] Gráfico guardado en cache para empresa {self.empresa.id}"
            )

        return result

    def get_ranking_tecnicos(self, top=5, force_refresh=False):
        """
        Retorna ranking de técnicos más productivos del mes actual.

        Args:
            top: Número de técnicos a retornar (default: 5)
            force_refresh: Forzar refresco (ignorar cache)

        Returns:
            QuerySet: Técnicos ordenados por total_generado descendente
        """
        cache_key = self._get_cache_key(f"ranking_tecnicos_{top}")

        # Intentar obtener de cache
        if self.cache_enabled and not force_refresh:
            cached = cache.get(cache_key)
            if cached is not None:
                log.debug(
                    f"[DashboardService] Ranking obtenido de cache para empresa {self.empresa.id}"
                )
                return cached

        # Importar aquí para evitar import circular
        from taller.models.tecnico import Tecnico

        # Agregación eficiente en DB
        # Filtrar técnicos que tienen documentos este mes y agregar métricas
        ranking = (
            Tecnico.objects.filter(empresa=self.empresa)
            .annotate(
                total_trabajos=Count(
                    "documentos_responsables",
                    filter=Q(
                        documentos_responsables__fecha_emision__gte=self.inicio_mes,
                        documentos_responsables__fecha_emision__lte=self.fin_mes,
                        documentos_responsables__estado="EMITIDO",
                    ),
                ),
                total_generado=Coalesce(
                    Sum(
                        "documentos_responsables__total",
                        filter=Q(
                            documentos_responsables__fecha_emision__gte=self.inicio_mes,
                            documentos_responsables__fecha_emision__lte=self.fin_mes,
                            documentos_responsables__estado="EMITIDO",
                        ),
                    ),
                    Decimal("0.00"),
                ),
            )
            .filter(total_trabajos__gt=0)  # Solo técnicos con trabajos
            .order_by("-total_generado")[:top]
        )

        # Convertir QuerySet a lista para cachear
        result = list(ranking)

        # Guardar en cache
        if self.cache_enabled:
            cache.set(cache_key, result, self.cache_timeout)
            log.debug(
                f"[DashboardService] Ranking guardado en cache para empresa {self.empresa.id}"
            )

        return result

    def invalidate_cache(self):
        """Invalida el cache del dashboard para esta empresa"""
        # Invalidar todas las claves relacionadas
        patterns = [
            "kpis_mes",
            "ventas_anuales",
            "ranking_tecnicos",
        ]

        for pattern in patterns:
            cache_key = self._get_cache_key(pattern)
            cache.delete(cache_key)

        log.info(f"[DashboardService] Cache invalidado para empresa {self.empresa.id}")
