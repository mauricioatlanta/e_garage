"""
Vistas para Dashboard de Inteligencia de Negocios (BI)
"""

import json
import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from taller.auth.decorators_role import RoleRequiredMixin
from taller.services.dashboard_service import DashboardService

log = logging.getLogger(__name__)


class DashboardHomeView(LoginRequiredMixin, RoleRequiredMixin, TemplateView):
    """
    Vista principal del Dashboard de BI.

    Features:
    - KPIs principales del mes
    - Gráfico de ventas anuales (12 meses)
    - Ranking de técnicos más productivos
    - Multi-tenant seguro
    - Caching automático
    - RBAC: Solo Owner y Admin pueden acceder
    """

    template_name = "taller/dashboard/home.html"
    allowed_roles = ["Owner", "Admin"]  # 🔒 Vendedores y Técnicos FUERA
    permission_denied_message = "Solo dueños y administradores pueden ver el Dashboard de BI."

    def get_context_data(self, **kwargs):
        """Obtiene datos del dashboard y los prepara para el template"""
        context = super().get_context_data(**kwargs)

        # Obtener empresa del usuario (multi-tenant)
        empresa = getattr(self.request.user, "empresa", None)
        if not empresa:
            log.warning(f"[DashboardBI] Usuario {self.request.user.id} sin empresa asociada")
            # Retornar contexto vacío si no hay empresa
            context["kpis"] = {}
            context["chart_labels"] = json.dumps([])
            context["chart_values"] = json.dumps([])
            context["top_tecnicos"] = []
            context["moneda"] = "$"
            return context

        # Inicializar servicio de dashboard
        force_refresh = self.request.GET.get("refresh", "").lower() == "true"
        service = DashboardService(empresa, cache_enabled=True, cache_timeout=3600)

        # 1. KPIs principales
        try:
            kpis = service.get_kpis_principales(force_refresh=force_refresh)
            context["kpis"] = kpis
        except Exception as e:
            log.error(f"[DashboardBI] Error obteniendo KPIs: {e}", exc_info=True)
            context["kpis"] = {
                "total_ventas": 0,
                "total_ot": 0,
                "total_facturas": 0,
                "total_presupuestos": 0,
                "ticket_promedio": 0,
                "tasa_conversion": 0,
            }

        # 2. Gráfico de ventas anuales (12 meses)
        try:
            meses = int(self.request.GET.get("meses", 12))
            chart_data = service.get_ventas_anuales_chart(meses=meses, force_refresh=force_refresh)
            # Serializar para JavaScript (Chart.js)
            context["chart_labels"] = json.dumps(chart_data["labels"], ensure_ascii=False)
            context["chart_values"] = json.dumps(chart_data["data"])
        except Exception as e:
            log.error(f"[DashboardBI] Error obteniendo gráfico: {e}", exc_info=True)
            context["chart_labels"] = json.dumps([])
            context["chart_values"] = json.dumps([])

        # 3. Ranking de técnicos
        try:
            top = int(self.request.GET.get("top", 5))
            context["top_tecnicos"] = service.get_ranking_tecnicos(
                top=top, force_refresh=force_refresh
            )
        except Exception as e:
            log.error(f"[DashboardBI] Error obteniendo ranking: {e}", exc_info=True)
            context["top_tecnicos"] = []

        # 4. Configuración de moneda según país
        pais = (empresa.pais or "CL").upper()
        if pais == "US":
            context["moneda"] = "US$"
        elif pais == "MX":
            context["moneda"] = "MX$"
        else:  # CL (Chile)
            context["moneda"] = "$"

        # 5. Información adicional para el template
        context["empresa"] = empresa
        context["pais"] = pais
        context["refresh_url"] = f"{self.request.path}?refresh=true"

        log.debug(f"[DashboardBI] Dashboard generado para empresa {empresa.id}")
        return context
