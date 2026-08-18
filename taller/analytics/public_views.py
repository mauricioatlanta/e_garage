from collections import Counter

from django.apps import apps
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.template.response import TemplateResponse

from taller.country.engine import URL_SLUG_TO_VERTICAL
from taller.models.public_page_view import PublicPageView


RUBRO_LABELS = {
    "workshop": "Taller mecánico",
    "salvage": "Desarmaduría",
    "parts": "Casa de repuestos",
    "carwash": "Carwash",
    "tire": "Vulcanización / Llantera",
}

COUNTRY_LABELS = {
    "cl": "Chile",
    "ar": "Argentina",
    "br": "Brasil",
    "co": "Colombia",
    "ec": "Ecuador",
    "mx": "México",
    "pe": "Perú",
    "uy": "Uruguay",
    "ve": "Venezuela",
    "us": "USA",
    "us_en": "USA",
    "us_es": "USA",
}


def es_staff_o_admin(user):
    return user.is_authenticated and (
        user.is_staff or user.is_superuser
    )


def _normalize_country(country):
    country = (country or "").strip().lower()

    if country in {"us_en", "us_es"}:
        return "us"

    return country


def _rubro_from_path(path):
    parts = [
        part
        for part in (path or "").split("/")
        if part
    ]

    for part in reversed(parts):
        vertical = URL_SLUG_TO_VERTICAL.get(part)
        if vertical:
            return vertical

    return ""


@login_required
@user_passes_test(es_staff_o_admin)
def public_analytics_dashboard(request):
    """
    Analytics de adquisición pública de eGarage.

    - Separa tráfico humano de bots.
    - Segmenta landings por país.
    - Segmenta landings por rubro.
    - Cruza país + rubro para decisiones de campañas.
    - Usa datos históricos existentes sin migración de DB:
      el rubro se deriva del slug/path de la landing.
    """

    qs_all = PublicPageView.objects.all()
    qs_human = qs_all.filter(is_bot=False)
    qs_bot = qs_all.filter(is_bot=True)

    total = qs_all.count()
    humanos = qs_human.count()
    bots = qs_bot.count()

    landings_humanas = qs_human.filter(
        page_type=PublicPageView.PAGE_LANDING
    )

    bienvenidas_humanas = qs_human.filter(
        page_type=PublicPageView.PAGE_WELCOME
    )

    home_humanas = qs_human.filter(
        page_type=PublicPageView.PAGE_HOME
    )

    # -------------------------------------------------------------
    # Países: unificar us_en + us_es como USA.
    # -------------------------------------------------------------
    pais_counter = Counter()

    for row in qs_human.exclude(country="").values(
        "country"
    ).annotate(
        total=Count("id")
    ):
        country = _normalize_country(row["country"])
        pais_counter[country] += row["total"]

    por_pais = [
        {
            "country": country,
            "label": COUNTRY_LABELS.get(
                country,
                country.upper(),
            ),
            "total": total_visitas,
        }
        for country, total_visitas in pais_counter.most_common()
    ]

    # -------------------------------------------------------------
    # Rubros: solo visitas humanas a landings.
    # -------------------------------------------------------------
    rubro_counter = Counter()

    # País + rubro.
    pais_rubro_counter = Counter()

    for visit in landings_humanas.only(
        "country",
        "path",
    ):
        rubro = _rubro_from_path(visit.path)

        if not rubro:
            continue

        country = _normalize_country(visit.country)

        rubro_counter[rubro] += 1

        if country:
            pais_rubro_counter[(country, rubro)] += 1

    por_rubro = [
        {
            "rubro": rubro,
            "label": RUBRO_LABELS.get(
                rubro,
                rubro.title(),
            ),
            "total": total_visitas,
        }
        for rubro, total_visitas in rubro_counter.most_common()
    ]

    pais_rubro = [
        {
            "country": country,
            "country_label": COUNTRY_LABELS.get(
                country,
                country.upper(),
            ),
            "rubro": rubro,
            "rubro_label": RUBRO_LABELS.get(
                rubro,
                rubro.title(),
            ),
            "total": total_visitas,
        }
        for (country, rubro), total_visitas
        in pais_rubro_counter.most_common()
    ]

    # -------------------------------------------------------------
    # Top landings humanas.
    # -------------------------------------------------------------
    paginas_top = (
        landings_humanas
        .values("path")
        .annotate(total=Count("id"))
        .order_by("-total")[:20]
    )

    # -------------------------------------------------------------
    # Bienvenidas por país.
    # -------------------------------------------------------------
    bienvenida_counter = Counter()

    for row in bienvenidas_humanas.values(
        "country"
    ).annotate(
        total=Count("id")
    ):
        country = _normalize_country(row["country"])

        if country:
            bienvenida_counter[country] += row["total"]

    por_bienvenida = [
        {
            "country": country,
            "label": COUNTRY_LABELS.get(
                country,
                country.upper(),
            ),
            "total": total_visitas,
        }
        for country, total_visitas
        in bienvenida_counter.most_common()
    ]

    # -------------------------------------------------------------
    # Tendencia: humanos + bots por día para detectar spikes de crawlers.
    # -------------------------------------------------------------
    tendencia = (
        qs_all
        .annotate(fecha=TruncDate("created_at"))
        .values("fecha")
        .annotate(
            humanos=Count("id", filter=Q(is_bot=False)),
            bots=Count("id", filter=Q(is_bot=True)),
        )
        .order_by("-fecha")[:30]
    )

    # -------------------------------------------------------------
    # Empresas reales: excluir cuentas demo/seed.
    # @egarage.test = dominio ficticio no deliverable (señal estructural).
    # nombre_taller iregex = convención de seed manual + Validation Center.
    # -------------------------------------------------------------
    Empresa = apps.get_model("taller", "Empresa")
    _DEMO_Q = (
        Q(nombre_taller__iregex=r"(prueba|demo)")
        | Q(user__email__endswith="@egarage.test")
    )
    qs_real = Empresa.objects.exclude(_DEMO_Q)

    # -------------------------------------------------------------
    # Empresas registradas por día (via fecha_inicio, solo reales).
    # -------------------------------------------------------------
    empresas_por_dia = (
        qs_real
        .annotate(dia=TruncDate("fecha_inicio"))
        .values("dia")
        .annotate(total=Count("id"))
        .order_by("-dia")[:15]
    )

    # -------------------------------------------------------------
    # Funnel de adquisición first-party (solo empresas reales).
    # -------------------------------------------------------------
    funnel = {
        "visitas":       humanos,
        "empresas":      qs_real.count(),
        "trials":        qs_real.filter(is_trial=True).count(),
        "suscripciones": qs_real.filter(
                             suscripcion_activa=True, is_trial=False
                         ).count(),
    }

    # -------------------------------------------------------------
    # Referrers: humanos, sin vacíos, top 15.
    # -------------------------------------------------------------
    por_referrer = list(
        qs_human
        .exclude(referrer="")
        .values("referrer")
        .annotate(total=Count("id"))
        .order_by("-total")[:15]
    )

    # -------------------------------------------------------------
    # Mobile vs desktop: humanos.
    # -------------------------------------------------------------
    _mob = {
        r["is_mobile"]: r["n"]
        for r in qs_human.values("is_mobile").annotate(n=Count("id"))
    }
    mobile_share = {
        "mobile":  _mob.get(True, 0),
        "desktop": _mob.get(False, 0),
    }

    # -------------------------------------------------------------
    # Idioma: humanos, sin vacíos.
    # -------------------------------------------------------------
    por_idioma = list(
        qs_human
        .exclude(language="")
        .values("language")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    context = {
        "total": total,
        "humanos": humanos,
        "bots": bots,
        "landings_humanas": landings_humanas.count(),
        "bienvenidas_humanas": bienvenidas_humanas.count(),
        "home_humanas": home_humanas.count(),
        "por_pais": por_pais,
        "por_rubro": por_rubro,
        "pais_rubro": pais_rubro,
        "por_bienvenida": por_bienvenida,
        "paginas_top": paginas_top,
        "tendencia": tendencia,
        "funnel": funnel,
        "por_referrer": por_referrer,
        "mobile_share": mobile_share,
        "por_idioma": por_idioma,
        "empresas_por_dia": empresas_por_dia,
    }

    return TemplateResponse(
        request,
        "analytics/public_dashboard.html",
        context,
    )
