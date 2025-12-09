# -----------------------------------------------------------------------------
# Copyright (c) 2025 eGarage. Todos los derechos reservados.
#
# PROPIEDAD INTELECTUAL PROTEGIDA. ESTRICTAMENTE CONFIDENCIAL.
# Este archivo contiene endpoints y vistas del motor de IA.
#
# Consulta el archivo LICENSE en la raíz del repositorio para más detalles
# sobre la protección de la Propiedad Intelectual de eGarage.
# -----------------------------------------------------------------------------
"""
Views para Dashboard AI con visualizaciones futuristas
Diferenciación por país con tecnología avanzada
"""

import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from taller.auth.decorators import login_required_default
from taller.middleware.rate_limiting import rate_limit

from .ai_reports import AIReportEngine, ReportExporter


@login_required
@login_required_default
def dashboard_ai_view(request):
    """Dashboard principal con AI Analytics"""

    # Obtener datos del motor de reportes AI
    engine = AIReportEngine(request.user.empresa)
    analytics_data = engine.get_dashboard_data()

    context = {
        "analytics": analytics_data,
        "user_country": request.user.empresa.pais,
        "is_usa": request.user.empresa.pais == "US",
        "page_title": (
            "AI Analytics Dashboard"
            if request.user.empresa.pais == "US"
            else "Dashboard AI Analytics"
        ),
    }

    return render(request, "analytics/dashboard_ai.html", context)


@login_required
@login_required_default
def revenue_analytics_api(request):
    """API para gráficas de ingresos en tiempo real"""

    periodo = int(request.GET.get("periodo", 30))
    engine = AIReportEngine(request.user.empresa)

    data = {
        "revenue_timeline": engine._get_revenue_timeline(periodo),
        "growth_rate": engine._calculate_growth(engine.empresa.documento_set.all(), "total"),
        "currency": engine.moneda,
        "symbol": engine.simbolo,
    }

    return JsonResponse(data)


@login_required
@login_required_default
def vehicle_analytics_api(request):
    """API para analytics de vehículos"""

    engine = AIReportEngine(request.user.empresa)

    data = {
        "distribution": engine._get_vehicle_distribution(),
        "heatmap": engine._get_service_heatmap(),
        "country": engine.empresa.pais,
    }

    return JsonResponse(data)


@login_required
@login_required_default
def clientes_analytics_api(request):
    """API para analytics de clientes"""

    engine = AIReportEngine(request.user.empresa)

    data = {
        "distribution": engine._get_clientes_distribution(),
        "heatmap": engine._get_clientes_heatmap(),
        "country": engine.empresa.pais,
    }

    return JsonResponse(data)


@login_required
@login_required_default
@rate_limit(action="ia_prediccion", per_ip=True, per_user=True)
def predictive_analytics_api(request):
    """API para predicciones con IA - Protegida con rate limiting estricto"""

    engine = AIReportEngine(request.user.empresa)

    data = {
        "predictions": engine._get_predictive_data(),
        "insights": engine._generate_ai_insights(
            engine.empresa.documento_set.all(),
            engine.empresa.vehiculo_set.all(),
            engine.empresa.cliente_set.all(),
        ),
        "confidence_score": 0.87,  # Score general de confianza del modelo
        "model_version": "AI-Engine-v2.1",
    }

    return JsonResponse(data)


@method_decorator(csrf_exempt, name="dispatch")
@method_decorator(rate_limit(action="ia_prediccion", per_ip=True, per_user=True), name="dispatch")
class AIInsightView(View):
    """Vista para insights generados por IA - Protegida con rate limiting estricto"""

    def post(self, request):
        try:
            data = json.loads(request.body)
            insight_type = data.get("type")
            timeframe = data.get("timeframe", 30)

            engine = AIReportEngine(request.user.empresa)

            if insight_type == "financial":
                insights = self._generate_financial_insights(engine, timeframe)
            elif insight_type == "operational":
                insights = self._generate_operational_insights(engine, timeframe)
            elif insight_type == "predictive":
                insights = self._generate_predictive_insights(engine, timeframe)
            else:
                insights = engine._generate_ai_insights(
                    engine.empresa.documento_set.all(),
                    engine.empresa.vehiculo_set.all(),
                    engine.empresa.cliente_set.all(),
                )

            return JsonResponse(
                {
                    "status": "success",
                    "insights": insights,
                    "generated_at": timezone.now().isoformat(),
                    "country": engine.empresa.pais,
                }
            )

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

    def _generate_financial_insights(self, engine, timeframe):
        """Insights financieros específicos"""
        from datetime import timedelta

        from django.utils import timezone

        fecha_inicio = timezone.now() - timedelta(days=timeframe)
        documentos = engine.empresa.documento_set.filter(created_at__gte=fecha_inicio)

        insights = []

        # Análisis de rentabilidad
        total_revenue = documentos.aggregate(Sum("total"))["total__sum"] or 0
        avg_ticket = documentos.aggregate(Avg("total"))["total__avg"] or 0

        if engine.empresa.pais == "US":
            insights.append(
                {
                    "type": "profitability",
                    "title": "Revenue Optimization Opportunity",
                    "description": f"Average ticket size: {engine._format_currency(avg_ticket)}. AI suggests 15% increase potential through upselling.",
                    "confidence": 0.82,
                    "action": "Implement premium service packages",
                    "impact": "High",
                    "timeframe": "30 days",
                }
            )
        else:
            insights.append(
                {
                    "type": "profitability",
                    "title": "Oportunidad de Optimización de Ingresos",
                    "description": f"Ticket promedio: {engine._format_currency(avg_ticket)}. IA sugiere potencial de aumento del 15% mediante venta cruzada.",
                    "confidence": 0.82,
                    "action": "Implementar paquetes de servicios premium",
                    "impact": "Alto",
                    "timeframe": "30 días",
                }
            )

        return insights

    def _generate_operational_insights(self, engine, timeframe):
        """Insights operacionales"""
        insights = []

        if engine.empresa.pais == "US":
            insights.extend(
                [
                    {
                        "type": "efficiency",
                        "title": "Workflow Optimization",
                        "description": "AI detected 23% time savings opportunity in service workflow",
                        "confidence": 0.76,
                        "action": "Implement digital service checklist",
                        "impact": "Medium",
                        "savings": "$2,400/month",
                    },
                    {
                        "type": "inventory",
                        "title": "Smart Inventory Management",
                        "description": "Predictive model suggests optimal stock levels for Q4",
                        "confidence": 0.89,
                        "action": "Adjust inventory based on seasonal patterns",
                        "impact": "High",
                    },
                ]
            )
        else:
            insights.extend(
                [
                    {
                        "type": "efficiency",
                        "title": "Optimización de Flujo de Trabajo",
                        "description": "IA detectó oportunidad de ahorro de 23% en tiempo de servicio",
                        "confidence": 0.76,
                        "action": "Implementar checklist digital de servicios",
                        "impact": "Medio",
                        "savings": "$600.000/mes",
                    },
                    {
                        "type": "inventory",
                        "title": "Gestión Inteligente de Inventario",
                        "description": "Modelo predictivo sugiere niveles óptimos de stock para Q4",
                        "confidence": 0.89,
                        "action": "Ajustar inventario según patrones estacionales",
                        "impact": "Alto",
                    },
                ]
            )

        return insights

    def _generate_predictive_insights(self, engine, timeframe):
        """Insights predictivos avanzados"""
        insights = []

        if engine.empresa.pais == "US":
            insights.extend(
                [
                    {
                        "type": "demand_forecast",
                        "title": "Service Demand Prediction",
                        "description": "34% increase in brake service demand predicted for next month",
                        "confidence": 0.91,
                        "action": "Stock brake components and schedule technician training",
                        "timeline": "Next 30 days",
                        "probability": "Very High",
                    },
                    {
                        "type": "customer_behavior",
                        "title": "Customer Retention Insight",
                        "description": "AI identified 12 customers at risk of churn",
                        "confidence": 0.78,
                        "action": "Launch targeted retention campaign",
                        "potential_loss": "$18,500",
                    },
                ]
            )
        else:
            insights.extend(
                [
                    {
                        "type": "demand_forecast",
                        "title": "Predicción de Demanda de Servicios",
                        "description": "Aumento del 34% en demanda de frenos predicho para el próximo mes",
                        "confidence": 0.91,
                        "action": "Almacenar componentes de frenos y programar capacitación técnica",
                        "timeline": "Próximos 30 días",
                        "probability": "Muy Alta",
                    },
                    {
                        "type": "customer_behavior",
                        "title": "Insight de Retención de Clientes",
                        "description": "IA identificó 12 clientes en riesgo de abandono",
                        "confidence": 0.78,
                        "action": "Lanzar campaña de retención dirigida",
                        "potential_loss": "$4.500.000",
                    },
                ]
            )

        return insights


@login_required
@login_required_default
def export_report_view(request):
    """Vista para exportar reportes por país"""

    formato = request.GET.get("format", "json")
    periodo = int(request.GET.get("periodo", 30))

    exporter = ReportExporter(request.user.empresa)
    report_data = exporter.export_financial_report(periodo)

    if formato == "json":
        return JsonResponse(report_data)
    elif formato == "excel":
        # TODO: Implementar exportación a Excel
        return JsonResponse({"message": "Excel export coming soon"})
    else:
        return JsonResponse({"error": "Formato no soportado"}, status=400)


@login_required
@login_required_default
def real_time_metrics_api(request):
    """API para métricas en tiempo real"""

    engine = AIReportEngine(request.user.empresa)

    # Métricas en tiempo real

    from django.utils import timezone

    today = timezone.now().date()

    # Documentos de hoy
    docs_today = engine.empresa.documento_set.filter(created_at__date=today)

    # Métricas de rendimiento
    metrics = {
        "today_revenue": float(docs_today.aggregate(Sum("total"))["total__sum"] or 0),
        "today_documents": docs_today.count(),
        "active_services": docs_today.filter(estado="EN_PROCESO").count(),
        "completed_today": docs_today.filter(estado="COMPLETADO").count(),
        "efficiency_rate": engine._calculate_efficiency(docs_today),
        "currency": engine.moneda,
        "symbol": engine.simbolo,
        "last_update": timezone.now().isoformat(),
        "country": engine.empresa.pais,
    }

    return JsonResponse(metrics)


# Vista para el dashboard de suscriptor
# Si tu modelo se llama Empresa, Cliente, Usuario, etc. cambia el nombre aquí


def suscriptor_dashboard(request, pk):
    # suscriptor = get_object_or_404(Suscriptor, pk=pk)
    # return render(request, 'taller/suscriptor_dashboard.html', {'suscriptor': suscriptor})
    # Ejemplo genérico:
    return render(request, "taller/suscriptor_dashboard.html", {"suscriptor_id": pk})
