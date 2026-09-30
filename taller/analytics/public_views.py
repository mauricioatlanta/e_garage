from collections import Counter

from django.apps import apps
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.template.response import TemplateResponse

from taller.country.engine import URL_SLUG_TO_VERTICAL
from taller.models.public_analytics_event import PublicAnalyticsEvent
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


def _count_event_sessions(event_types):
    events = PublicAnalyticsEvent.objects.filter(
        event_type__in=event_types,
        is_bot=False,
        is_internal=False,
    )
    with_session = events.exclude(session_id__isnull=True).values("session_id").distinct().count()
    without_session = events.filter(session_id__isnull=True).count()
    return with_session + without_session


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
    qs_human = qs_all.filter(is_bot=False, is_internal=False)
    qs_bot = qs_all.filter(is_bot=True)

    total = qs_all.count()
    humanos = qs_human.count()
    bots = qs_bot.count()

    burst_threshold = 20
    burst_visitors = list(
        qs_human.values("visitor_hash")
        .annotate(total=Count("id"))
        .filter(total__gte=burst_threshold)
        .values_list("visitor_hash", flat=True)
    )
    visitas_rafaga = (
        qs_human.filter(visitor_hash__in=burst_visitors).count()
        if burst_visitors
        else 0
    )
    prospectos_estimados = max(humanos - visitas_rafaga, 0)

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

    RegistroEmbudoSuscriptor = apps.get_model("taller", "RegistroEmbudoSuscriptor")
    attributed_embudos = RegistroEmbudoSuscriptor.objects.filter(
        public_session__isnull=False,
        public_session__is_bot=False,
        public_session__is_internal=False,
    ).exclude(
        Q(user__empresa__nombre_taller__iregex=r"(prueba|demo)")
        | Q(user__email__endswith="@egarage.test")
    )
    attributed_empresa_user_ids = attributed_embudos.filter(
        empresa_creada_at__isnull=False,
        user__empresa__isnull=False,
    ).values_list("user_id", flat=True)

    landing_sessions = landings_humanas.exclude(public_session_id__isnull=True).values(
        "public_session_id"
    ).distinct().count()
    utm_sessions = attributed_embudos.filter(
        Q(public_session__utm_source__gt="")
        | Q(public_session__utm_medium__gt="")
        | Q(public_session__utm_campaign__gt="")
    ).values("public_session_id").distinct().count()
    attributed_companies = attributed_empresa_user_ids.count()
    attributed_trials = qs_real.filter(
        user_id__in=attributed_empresa_user_ids,
        is_trial=True,
    ).count()
    attributed_subscriptions = qs_real.filter(
        user_id__in=attributed_empresa_user_ids,
        suscripcion_activa=True,
        is_trial=False,
    ).count()
    attributed_conversion_rate = (
        round((attributed_companies / landing_sessions) * 100, 2)
        if landing_sessions
        else 0
    )

    # -------------------------------------------------------------
    # Funnel de adquisición first-party atribuido.
    # -------------------------------------------------------------
    funnel = {
        "visitas": prospectos_estimados,
        "sesiones_landing": landing_sessions,
        "sesiones_utm": utm_sessions,
        "empresas": attributed_companies,
        "trials": attributed_trials,
        "suscripciones": attributed_subscriptions,
        "tasa_conversion": attributed_conversion_rate,
    }

    crecimiento_global = {
        "empresas": qs_real.count(),
        "trials": qs_real.filter(is_trial=True).count(),
        "suscripciones": qs_real.filter(
            suscripcion_activa=True,
            is_trial=False,
        ).count(),
        "altas_atribuidas": attributed_companies,
        "altas_sin_atribucion": max(qs_real.count() - attributed_companies, 0),
    }

    eventos_funnel = {
        "cta_clicks": _count_event_sessions(
            [
                PublicAnalyticsEvent.EVENT_CTA_CLICK,
                PublicAnalyticsEvent.EVENT_CTA_WHATSAPP_CLICK,
                PublicAnalyticsEvent.EVENT_CTA_TRIAL_30_CLICK,
            ]
        ),
        "signup_starts": _count_event_sessions(
            [
                PublicAnalyticsEvent.EVENT_SIGNUP_START,
                PublicAnalyticsEvent.EVENT_SIGNUP_STARTED,
            ]
        ),
        "signup_completes": _count_event_sessions(
            [
                PublicAnalyticsEvent.EVENT_SIGNUP_COMPLETE,
                PublicAnalyticsEvent.EVENT_SIGNUP_COMPLETED,
            ]
        ),
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
        "visitas_rafaga": visitas_rafaga,
        "prospectos_estimados": prospectos_estimados,
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
        "crecimiento_global": crecimiento_global,
        "eventos_funnel": eventos_funnel,
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
