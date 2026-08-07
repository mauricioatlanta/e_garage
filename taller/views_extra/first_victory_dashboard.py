from datetime import timedelta

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Min, OuterRef, Subquery
from django.shortcuts import render
from django.utils import timezone

from taller.models.configuracion import ConfiguracionEmpresa
from taller.models.empresa import Empresa
from taller.models.repuesto import Repuesto
from taller.models.vehiculo_desarme import VehiculoDesarme
from taller.models.vehiculos import Vehiculo

try:
    from allauth.account.models import EmailAddress
    _ALLAUTH_AVAILABLE = True
except ImportError:
    _ALLAUTH_AVAILABLE = False

# Rubros que usan Vehiculo como Primera Victoria
_WORKSHOP_RUBROS = {"WORKSHOP", "WORKSHOP_MOTO", "WORKSHOP_HEAVY"}


def _primera_victoria_at(empresa, rubro):
    """Returns datetime of Primera Victoria for an empresa, or None."""
    if rubro in _WORKSHOP_RUBROS:
        obj = Vehiculo.objects.filter(empresa=empresa).order_by("created_at").values("created_at").first()
    elif rubro == "DESARMADURIA":
        obj = VehiculoDesarme.objects.filter(empresa=empresa).order_by("created_at").values("created_at").first()
    elif rubro == "PARTS":
        obj = Repuesto.objects.filter(empresa=empresa).order_by("created_at").values("created_at").first()
    else:
        return None
    return obj["created_at"] if obj else None


def _build_funnel(empresas_qs):
    """
    Given a queryset of Empresa, compute funnel stats.
    Returns a list of per-empresa dicts and summary counts.
    """
    empresas = list(
        empresas_qs.select_related("config", "user").order_by("-fecha_inicio")
    )

    # Email confirmations — one query
    if _ALLAUTH_AVAILABLE:
        confirmed_user_ids = set(
            EmailAddress.objects.filter(verified=True, primary=True)
            .values_list("user_id", flat=True)
        )
    else:
        confirmed_user_ids = set()

    rows = []
    for empresa in empresas:
        try:
            rubro = empresa.config.rubro_principal
        except ConfiguracionEmpresa.DoesNotExist:
            rubro = None

        email_ok = empresa.user_id in confirmed_user_ids
        victoria_at = _primera_victoria_at(empresa, rubro)
        time_to_victoria = None
        if victoria_at and empresa.fecha_inicio:
            delta = victoria_at - empresa.fecha_inicio
            time_to_victoria = delta.total_seconds() / 60  # minutes

        rows.append({
            "empresa": empresa,
            "rubro": rubro or "—",
            "fecha_inicio": empresa.fecha_inicio,
            "email_ok": email_ok,
            "victoria_at": victoria_at,
            "time_to_victoria_min": time_to_victoria,
        })

    return rows


def _rubro_label(key):
    labels = {
        "WORKSHOP": "Taller",
        "WORKSHOP_MOTO": "Taller (motos)",
        "WORKSHOP_HEAVY": "Taller (pesados)",
        "DESARMADURIA": "Desarmaduría",
        "PARTS": "Casa de Repuestos",
        "TIRE": "Vulcanización",
        "BODYSHOP": "Hojalatería",
        "DETAILING": "Detailing",
        "ELECTRIC": "Eléctrico",
    }
    return labels.get(key, key or "Sin rubro")


def _aggregate(rows):
    """Compute Panel 1 + Panel 2 + Panel 3 from rows."""
    total = len(rows)
    confirmed = sum(1 for r in rows if r["email_ok"])
    victorias = [r for r in rows if r["victoria_at"]]
    sin_victoria = [r for r in rows if r["email_ok"] and not r["victoria_at"]]

    # Panel 2 — por rubro (Foundation rubros primero)
    FOUNDATION_ORDER = ["WORKSHOP", "WORKSHOP_MOTO", "WORKSHOP_HEAVY", "DESARMADURIA", "PARTS"]
    rubros_seen = {}
    for r in rows:
        rk = r["rubro"] if r["rubro"] != "—" else "UNKNOWN"
        if rk not in rubros_seen:
            rubros_seen[rk] = {"rubro_key": rk, "signups": 0, "confirmados": 0, "victorias": 0, "tiempos": []}
        rubros_seen[rk]["signups"] += 1
        if r["email_ok"]:
            rubros_seen[rk]["confirmados"] += 1
        if r["victoria_at"]:
            rubros_seen[rk]["victorias"] += 1
            if r["time_to_victoria_min"] is not None:
                rubros_seen[rk]["tiempos"].append(r["time_to_victoria_min"])

    rubro_stats = []
    for rk in FOUNDATION_ORDER:
        if rk in rubros_seen:
            rd = rubros_seen.pop(rk)
            rd["label"] = _rubro_label(rk)
            rd["conversion_pct"] = round(rd["victorias"] * 100 / rd["signups"]) if rd["signups"] else 0
            rd["mediana_min"] = _median(rd["tiempos"])
            rubro_stats.append(rd)
    # remaining rubros
    for rk, rd in rubros_seen.items():
        rd["label"] = _rubro_label(rk)
        rd["conversion_pct"] = round(rd["victorias"] * 100 / rd["signups"]) if rd["signups"] else 0
        rd["mediana_min"] = _median(rd["tiempos"])
        rubro_stats.append(rd)

    # Panel 3 — tiempo global
    all_times = [r["time_to_victoria_min"] for r in victorias if r["time_to_victoria_min"] is not None]
    mediana_global = _median(all_times)
    promedio_global = round(sum(all_times) / len(all_times)) if all_times else None

    # FVI
    fvi_pct = round(len(victorias) * 100 / total) if total else 0

    return {
        "total": total,
        "confirmed": confirmed,
        "confirmed_pct": round(confirmed * 100 / total) if total else 0,
        "victorias": len(victorias),
        "victorias_pct": round(len(victorias) * 100 / confirmed) if confirmed else 0,
        "sin_victoria": len(sin_victoria),
        "fvi_pct": fvi_pct,
        "rubro_stats": rubro_stats,
        "mediana_global_min": mediana_global,
        "promedio_global_min": promedio_global,
    }


def _blocked(rows, cutoff_hours=24):
    """Panel 4 — empresas sin email confirmado o sin victoria después de N horas."""
    now = timezone.now()
    cutoff = now - timedelta(hours=cutoff_hours)
    unconfirmed = []
    stalled = []
    for r in rows:
        if not r["fecha_inicio"]:
            continue
        age_ok = r["fecha_inicio"] <= cutoff
        if not age_ok:
            continue
        if not r["email_ok"]:
            unconfirmed.append(r)
        elif not r["victoria_at"]:
            stalled.append(r)
    return unconfirmed, stalled


def _median(lst):
    if not lst:
        return None
    s = sorted(lst)
    n = len(s)
    mid = n // 2
    if n % 2 == 0:
        return round((s[mid - 1] + s[mid]) / 2)
    return round(s[mid])


def _fmt_minutes(m):
    if m is None:
        return "—"
    if m < 60:
        return f"{m} min"
    h = m // 60
    mn = m % 60
    return f"{h}h {mn}m" if mn else f"{h}h"


@staff_member_required
def first_victory_dashboard(request):
    period = request.GET.get("period", "30d")

    now = timezone.now()
    if period == "7d":
        since = now - timedelta(days=7)
        period_label = "Últimos 7 días"
    elif period == "30d":
        since = now - timedelta(days=30)
        period_label = "Últimos 30 días"
    else:
        since = None
        period_label = "Todo el tiempo"

    qs = Empresa.objects.all()
    if since:
        qs = qs.filter(fecha_inicio__gte=since)

    rows = _build_funnel(qs)
    stats = _aggregate(rows)
    unconfirmed, stalled = _blocked(rows)

    # Format time stats for display
    for rs in stats["rubro_stats"]:
        rs["mediana_fmt"] = _fmt_minutes(rs["mediana_min"])

    context = {
        "period": period,
        "period_label": period_label,
        "stats": stats,
        "unconfirmed": unconfirmed[:20],
        "stalled": stalled[:20],
        "fvi_fmt": _fmt_minutes(stats["mediana_global_min"]),
        "rows": rows[:50],
    }
    return render(request, "staff/first_victory.html", context)
