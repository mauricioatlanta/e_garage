from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.views.generic import ListView

from core.views import TenantViewMixin
from taller.models.repuesto import Repuesto
from taller.services.inventory_intelligence import InventoryIntelligenceService


class ReabastecimientoPanelView(LoginRequiredMixin, TenantViewMixin, ListView):
    model = Repuesto
    template_name = "taller/repuestos/reabastecimiento.html"
    context_object_name = "repuestos"
    select_related_fields = ("categoria",)
    paginate_by = None

    def get_queryset(self):
        qs = super().get_queryset()
        q = (self.request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(
                models.Q(part_number__icontains=q)
                | models.Q(nombre__icontains=q)
                | models.Q(proveedor__icontains=q)
                | models.Q(categoria__nombre__icontains=q)
            )
        return qs.order_by("nombre", "id")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa = getattr(self.request.user, "empresa", None)
        status_filter = (self.request.GET.get("status") or "").strip().lower()
        panel = InventoryIntelligenceService.build_panel(
            empresa=empresa,
            queryset=context["object_list"],
            lookback_days=InventoryIntelligenceService.DEFAULT_LOOKBACK_DAYS,
            target_coverage_days=InventoryIntelligenceService.DEFAULT_TARGET_COVERAGE_DAYS,
        )
        rows = panel["rows"]
        if status_filter in {"critical", "warning", "stable", "idle"}:
            rows = [row for row in rows if row["status"] == status_filter]

        context.update(
            {
                "panel_rows": rows,
                "panel_summary": panel["summary"],
                "status_filter": status_filter,
                "lookback_days": panel["lookback_days"],
                "target_coverage_days": panel["target_coverage_days"],
                "search_query": (self.request.GET.get("q") or "").strip(),
            }
        )
        return context
