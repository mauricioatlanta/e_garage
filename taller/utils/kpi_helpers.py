"""
Utilidades para KPIs optimizadas con patrones ORM eficientes.
Patrones recomendados para eGarage.
"""

from datetime import timedelta

from django.db.models import Avg, Count, DecimalField, ExpressionWrapper, F, Q, Sum
from django.db.models.functions import TruncMonth, TruncYear
from django.utils import timezone


class KPIHelpers:
    """Clase helper para cálculos de KPIs optimizados."""

    @staticmethod
    def get_monto_calculado():
        """
        Patrón estándar para calcular monto con descuento.
        Usar en todos los KPIs que involucren líneas de documento.
        """
        return ExpressionWrapper(
            F("cantidad") * F("precio_unitario") * (1 - F("descuento") / 100),
            output_field=DecimalField(max_digits=14, decimal_places=2),
        )

    @staticmethod
    def get_responsable_calculado():
        """
        Patrón estándar para obtener responsable.
        Como las líneas no tienen campo 'responsable', siempre usa el del documento.
        """
        return F("documento__tecnico_responsable")

    @staticmethod
    def get_filtro_fecha_emision(fecha_inicio=None, fecha_fin=None):
        """
        Patrón estándar para filtrar por fecha_emision.
        SIEMPRE usar fecha_emision, nunca created/updated.
        """
        filtro = Q()

        if fecha_inicio:
            filtro &= Q(documento__fecha_emision__gte=fecha_inicio)

        if fecha_fin:
            filtro &= Q(documento__fecha_emision__lte=fecha_fin)

        return filtro

    @staticmethod
    def get_filtro_empresa(empresa):
        """
        Patrón estándar para filtrar por empresa.
        """
        return Q(documento__empresa=empresa)

    @staticmethod
    def get_filtro_mes_actual():
        """
        Patrón estándar para filtrar por mes actual.
        """
        ahora = timezone.now()
        return Q(
            documento__fecha_emision__year=ahora.year,
            documento__fecha_emision__month=ahora.month,
        )

    @staticmethod
    def get_filtro_ano_actual():
        """
        Patrón estándar para filtrar por año actual.
        """
        ahora = timezone.now()
        return Q(documento__fecha_emision__year=ahora.year)


class KPICalculator:
    """Calculadora de KPIs con patrones optimizados."""

    def __init__(self, empresa=None):
        self.empresa = empresa
        self.monto_calculado = KPIHelpers.get_monto_calculado()
        self.responsable_calculado = KPIHelpers.get_responsable_calculado()

    def get_totales_por_tecnico(self, fecha_inicio=None, fecha_fin=None):
        """
        KPI: Totales por técnico en un período.
        Patrón optimizado con índices.
        """
        from taller.models import LineaServicio

        filtro = KPIHelpers.get_filtro_fecha_emision(fecha_inicio, fecha_fin)

        if self.empresa:
            filtro &= KPIHelpers.get_filtro_empresa(self.empresa)

        return (
            LineaServicio.objects.filter(filtro)
            .annotate(monto=self.monto_calculado)
            .values("documento__tecnico_responsable__nombre")
            .annotate(
                total=Sum("monto"),
                cantidad_documentos=Count("documento", distinct=True),
                cantidad_lineas=Count("id"),
            )
            .order_by("-total")
        )

    def get_totales_por_servicio(self, fecha_inicio=None, fecha_fin=None):
        """
        KPI: Totales por servicio en un período.
        """
        from taller.models import LineaServicio

        filtro = KPIHelpers.get_filtro_fecha_emision(fecha_inicio, fecha_fin)

        if self.empresa:
            filtro &= KPIHelpers.get_filtro_empresa(self.empresa)

        return (
            LineaServicio.objects.filter(filtro)
            .annotate(monto=self.monto_calculado)
            .values("servicio__nombre")
            .annotate(
                total=Sum("monto"), cantidad_veces=Count("id"), promedio=Avg("monto")
            )
            .order_by("-total")
        )

    def get_documentos_por_estado(self, fecha_inicio=None, fecha_fin=None):
        """
        KPI: Documentos por estado en un período.
        """
        from taller.models import Documento

        filtro = Q()

        if fecha_inicio:
            filtro &= Q(fecha_emision__gte=fecha_inicio)

        if fecha_fin:
            filtro &= Q(fecha_emision__lte=fecha_fin)

        if self.empresa:
            filtro &= Q(empresa=self.empresa)

        return (
            Documento.objects.filter(filtro)
            .values("estado")
            .annotate(cantidad=Count("id"), total_monto=Sum("total"))
            .order_by("-cantidad")
        )

    def get_tecnicos_mas_activos(self, fecha_inicio=None, fecha_fin=None):
        """
        KPI: Técnicos más activos por cantidad de documentos.
        """
        from taller.models import Tecnico

        filtro = Q()

        if fecha_inicio:
            filtro &= Q(documentos_responsables__fecha_emision__gte=fecha_inicio)

        if fecha_fin:
            filtro &= Q(documentos_responsables__fecha_emision__lte=fecha_fin)

        if self.empresa:
            filtro &= Q(empresa=self.empresa)

        return (
            Tecnico.objects.filter(filtro)
            .annotate(
                cantidad_documentos=Count("documentos_responsables", distinct=True),
                cantidad_lineas=Count("documentos_responsables__lineas_servicio"),
            )
            .order_by("-cantidad_documentos")
        )

    def get_rendimiento_mensual(self, meses=12):
        """
        KPI: Rendimiento mensual de los últimos N meses.
        """
        from taller.models import LineaServicio

        fecha_inicio = timezone.now() - timedelta(days=meses * 30)

        filtro = KPIHelpers.get_filtro_fecha_emision(fecha_inicio)

        if self.empresa:
            filtro &= KPIHelpers.get_filtro_empresa(self.empresa)

        return (
            LineaServicio.objects.filter(filtro)
            .annotate(
                mes=TruncMonth("documento__fecha_emision"), monto=self.monto_calculado
            )
            .values("mes")
            .annotate(
                total=Sum("monto"),
                cantidad_documentos=Count("documento", distinct=True),
            )
            .order_by("mes")
        )

    def get_rendimiento_anual(self, anos=3):
        """
        KPI: Rendimiento anual de los últimos N años.
        """
        from taller.models import LineaServicio

        fecha_inicio = timezone.now() - timedelta(days=anos * 365)

        filtro = KPIHelpers.get_filtro_fecha_emision(fecha_inicio)

        if self.empresa:
            filtro &= KPIHelpers.get_filtro_empresa(self.empresa)

        return (
            LineaServicio.objects.filter(filtro)
            .annotate(
                ano=TruncYear("documento__fecha_emision"), monto=self.monto_calculado
            )
            .values("ano")
            .annotate(
                total=Sum("monto"),
                cantidad_documentos=Count("documento", distinct=True),
            )
            .order_by("ano")
        )

    def get_clientes_mas_activos(self, fecha_inicio=None, fecha_fin=None, limite=10):
        """
        KPI: Clientes más activos por cantidad de documentos.
        """
        from taller.models import Cliente

        filtro = Q()

        if fecha_inicio:
            filtro &= Q(documentos__fecha_emision__gte=fecha_inicio)

        if fecha_fin:
            filtro &= Q(documentos__fecha_emision__lte=fecha_fin)

        if self.empresa:
            filtro &= Q(empresa=self.empresa)

        return (
            Cliente.objects.filter(filtro)
            .annotate(
                cantidad_documentos=Count("documentos", distinct=True),
                total_monto=Sum("documentos__total"),
            )
            .order_by("-cantidad_documentos")[:limite]
        )

    def get_vehiculos_mas_serviciados(
        self, fecha_inicio=None, fecha_fin=None, limite=10
    ):
        """
        KPI: Vehículos más serviciados.
        """
        from taller.models import Vehiculo

        filtro = Q()

        if fecha_inicio:
            filtro &= Q(documentos__fecha_emision__gte=fecha_inicio)

        if fecha_fin:
            filtro &= Q(documentos__fecha_emision__lte=fecha_fin)

        if self.empresa:
            filtro &= Q(empresa=self.empresa)

        return (
            Vehiculo.objects.filter(filtro)
            .annotate(
                cantidad_documentos=Count("documentos", distinct=True),
                total_monto=Sum("documentos__total"),
            )
            .order_by("-cantidad_documentos")[:limite]
        )


# Funciones de conveniencia para uso directo
def get_kpi_tecnico_mes_actual(empresa=None):
    """KPI rápido: técnico del mes actual."""
    calculator = KPICalculator(empresa)
    return calculator.get_totales_por_tecnico()


def get_kpi_servicio_mes_actual(empresa=None):
    """KPI rápido: servicio del mes actual."""
    calculator = KPICalculator(empresa)
    return calculator.get_totales_por_servicio()


def get_kpi_documentos_estado_mes_actual(empresa=None):
    """KPI rápido: documentos por estado del mes actual."""
    calculator = KPICalculator(empresa)
    return calculator.get_documentos_por_estado()


def get_kpi_rendimiento_mensual(empresa=None, meses=12):
    """KPI rápido: rendimiento mensual."""
    calculator = KPICalculator(empresa)
    return calculator.get_rendimiento_mensual(meses)
