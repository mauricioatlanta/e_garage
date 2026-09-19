import json
from collections import Counter
from datetime import timedelta
from urllib.parse import urlparse

from django.apps import apps
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.http import JsonResponse
from django.template.response import TemplateResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from taller.country.engine import URL_SLUG_TO_VERTICAL
from taller.models.public_page_view import PublicAnalyticsEvent, PublicPageView
from taller.services.public_analytics import create_public_event


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


def _percent(value, total):
    if not total:
        return 0
    return round((value / total) * 100, 1)


def _ratio(value, total):
    if not total:
        return 0
    return round(value / total, 1)


def _safe_days(raw_days):
    try:
        days = int(raw_days or 30)
    except (TypeError, ValueError):
        return 30

    return min(max(days, 1), 365)


def _source_from_referrer(referrer):
    if not referrer:
        return "Directo / sin referrer"

    netloc = urlparse(referrer).netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]

    if not netloc:
        return "Directo / sin referrer"

    if "google." in netloc:
        return "Google"
    if "bing." in netloc:
        return "Bing"
    if "facebook." in netloc or "instagram." in netloc:
        return "Meta"
    if "tiktok." in netloc:
        return "TikTok"
    if "linkedin." in netloc:
        return "LinkedIn"
    if "egarage.cl" in netloc:
        return "eGarage interno"

    return netloc


def _country_language_from_path_or_url(value):
    path = (value or "").strip()
    if not path:
        return "", ""
    try:
        parsed = urlparse(path)
        if parsed.path:
            path = parsed.path
    except Exception:
        pass
    parts = [part.lower() for part in path.split("/") if part]
    country = parts[0] if parts and len(parts[0]) == 2 else ""
    language = parts[1] if len(parts) >= 2 and len(parts[1]) == 2 else ""
    return country, language


@csrf_exempt
@require_POST
def track_public_event_api(request):
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        payload = {}

    event_type = (payload.get("event_type") or "").strip()
    allowed = {choice[0] for choice in PublicAnalyticsEvent.EVENT_TYPE_CHOICES}
    if event_type not in allowed:
        return JsonResponse({"ok": False, "error": "invalid_event_type"}, status=400)

    metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
    metadata.update({
        "label": (payload.get("label") or "")[:120],
        "target": (payload.get("target") or "")[:500],
    })
    inferred_country = (payload.get("country") or "").strip()[:8]
    inferred_language = (payload.get("language") or "").strip()[:8]
    if not inferred_country or not inferred_language:
        page_country, page_language = _country_language_from_path_or_url(
            metadata.get("page_path", "")
        )
        target_country, target_language = _country_language_from_path_or_url(
            metadata.get("target", "")
        )
        inferred_country = inferred_country or page_country or target_country
        inferred_language = inferred_language or page_language or target_language

    event = create_public_event(
        request,
        event_type,
        country=inferred_country,
        language=inferred_language,
        rubro=(payload.get("rubro") or "")[:40],
        metadata=metadata,
    )
    return JsonResponse({"ok": bool(event)})


@login_required
@user_passes_test(es_staff_o_admin)
def admin_visits_dashboard(request):
    """
    Panel ejecutivo de visitas públicas de eGarage.

    Usa telemetría first-party almacenada en PublicPageView, por lo que funciona
    aunque Google Analytics no tenga API configurada en el backend.
    """

    days = _safe_days(request.GET.get("days"))
    selected_country = _normalize_country(request.GET.get("country"))
    selected_rubro = (request.GET.get("rubro") or "").strip().lower()
    include_bots = request.GET.get("bots") == "1"

    now = timezone.now()
    since = now - timedelta(days=days)

    qs_all_period = PublicPageView.objects.filter(created_at__gte=since)
    qs_scope = qs_all_period.filter(is_internal=False)
    if not include_bots:
        qs_scope = qs_scope.filter(is_bot=False)

    if selected_country:
        country_filters = [selected_country]
        if selected_country == "us":
            country_filters.extend(["us_en", "us_es"])
        qs_scope = qs_scope.filter(country__in=country_filters)

    if selected_rubro:
        slugs = [
            slug
            for slug, vertical in URL_SLUG_TO_VERTICAL.items()
            if vertical == selected_rubro
        ]
        rubro_q = Q()
        for slug in slugs:
            rubro_q |= Q(path__icontains=f"/{slug}/")
        qs_scope = qs_scope.filter(rubro_q)

    qs_human_period = qs_all_period.filter(is_bot=False, is_internal=False)
    qs_bot_period = qs_all_period.filter(is_bot=True)
    qs_internal_period = qs_all_period.filter(is_internal=True)

    events_all = PublicAnalyticsEvent.objects.filter(created_at__gte=since, is_internal=False)
    if not include_bots:
        events_all = events_all.filter(is_bot=False)
    if selected_country:
        event_country_filters = [selected_country]
        if selected_country == "us":
            event_country_filters.extend(["us_en", "us_es"])
        events_all = events_all.filter(country__in=event_country_filters)
    if selected_rubro:
        events_all = events_all.filter(rubro=selected_rubro)

    total_visits = qs_scope.count()
    unique_visitors = qs_scope.values("visitor_hash").distinct().count()
    sessions = qs_scope.exclude(session_key="").values("session_key").distinct().count()
    mobile_visits = qs_scope.filter(is_mobile=True).count()
    landing_qs = qs_scope.filter(page_type=PublicPageView.PAGE_LANDING)
    landing_visits = landing_qs.count()
    landing_unique_visitors = landing_qs.values("visitor_hash").distinct().count()
    landing_sessions = landing_qs.exclude(session_key="").values("session_key").distinct().count()
    welcome_visits = qs_scope.filter(page_type=PublicPageView.PAGE_WELCOME).count()
    home_visits = qs_scope.filter(page_type=PublicPageView.PAGE_HOME).count()
    raw_visits = qs_all_period.count()
    raw_human_candidate_visits = qs_human_period.count()
    unknown_language_visits = qs_scope.filter(language="").count()
    direct_visits = qs_scope.filter(
        Q(source_label="") | Q(source_label__icontains="directo") | Q(source_label__icontains="sin referrer")
    ).count()
    visits_per_session = _ratio(total_visits, sessions)

    # Contexto de negocio: empresas reales creadas en el mismo período.
    Empresa = apps.get_model("taller", "Empresa")
    demo_q = (
        Q(nombre_taller__iregex=r"(prueba|demo)")
        | Q(user__email__endswith="@egarage.test")
    )
    empresas_period = Empresa.objects.exclude(demo_q).filter(fecha_inicio__gte=since)
    trials_period = empresas_period.filter(is_trial=True).count()
    paid_period = empresas_period.filter(suscripcion_activa=True, is_trial=False).count()

    trend_rows = list(
        qs_scope
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(
            visits=Count("id"),
            unique=Count("visitor_hash", distinct=True),
        )
        .order_by("day")
    )

    previous_since = since - timedelta(days=days)
    previous_qs = PublicPageView.objects.filter(
        created_at__gte=previous_since,
        created_at__lt=since,
    )
    previous_qs = previous_qs.filter(is_internal=False)
    if not include_bots:
        previous_qs = previous_qs.filter(is_bot=False)
    previous_total = previous_qs.count()
    trend_delta = _percent(total_visits - previous_total, previous_total)

    previous_events = PublicAnalyticsEvent.objects.filter(
        created_at__gte=previous_since,
        created_at__lt=since,
        is_internal=False,
    )
    if not include_bots:
        previous_events = previous_events.filter(is_bot=False)
    if selected_country:
        previous_event_country_filters = [selected_country]
        if selected_country == "us":
            previous_event_country_filters.extend(["us_en", "us_es"])
        previous_events = previous_events.filter(country__in=previous_event_country_filters)
    if selected_rubro:
        previous_events = previous_events.filter(rubro=selected_rubro)

    country_counter = Counter()
    for row in qs_scope.exclude(country="").values("country").annotate(total=Count("id")):
        country_counter[_normalize_country(row["country"])] += row["total"]

    countries = []
    for country, total in country_counter.most_common():
        countries.append({
            "country": country,
            "label": COUNTRY_LABELS.get(country, country.upper()),
            "total": total,
            "share": _percent(total, total_visits),
        })

    rubro_counter = Counter()
    country_rubro_counter = Counter()
    for visit in qs_scope.filter(page_type=PublicPageView.PAGE_LANDING).only("country", "path"):
        rubro = _rubro_from_path(visit.path)
        if not rubro:
            continue
        country = _normalize_country(visit.country)
        rubro_counter[rubro] += 1
        if country:
            country_rubro_counter[(country, rubro)] += 1

    rubros = [
        {
            "rubro": rubro,
            "label": RUBRO_LABELS.get(rubro, rubro.title()),
            "total": total,
            "share": _percent(total, landing_visits),
        }
        for rubro, total in rubro_counter.most_common()
    ]

    country_rubro = [
        {
            "country": country,
            "country_label": COUNTRY_LABELS.get(country, country.upper()),
            "rubro": rubro,
            "rubro_label": RUBRO_LABELS.get(rubro, rubro.title()),
            "total": total,
        }
        for (country, rubro), total in country_rubro_counter.most_common(20)
    ]

    page_type_rows = []
    page_type_labels = dict(PublicPageView.PAGE_TYPE_CHOICES)
    for row in qs_scope.values("page_type").annotate(total=Count("id")).order_by("-total"):
        page_type_rows.append({
            "page_type": row["page_type"],
            "label": page_type_labels.get(row["page_type"], row["page_type"]),
            "total": row["total"],
            "share": _percent(row["total"], total_visits),
        })

    top_pages = [
        {
            "path": row["path"],
            "total": row["total"],
            "unique": row["unique"],
            "share": _percent(row["total"], total_visits),
        }
        for row in (
            qs_scope
            .values("path")
            .annotate(total=Count("id"), unique=Count("visitor_hash", distinct=True))
            .order_by("-total")[:20]
        )
    ]

    entry_pages = [
        {
            "path": row["landing_initial"] or row["path"] or "N/D",
            "sessions": row["sessions"],
            "visits": row["visits"],
            "share": _percent(row["sessions"], sessions),
        }
        for row in (
            qs_scope
            .values("landing_initial", "path")
            .annotate(
                sessions=Count("session_key", distinct=True),
                visits=Count("id"),
            )
            .order_by("-sessions")[:15]
        )
    ]

    source_counter = Counter()
    for row in qs_scope.values("source_label").annotate(total=Count("id")):
        source_counter[row["source_label"] or "Directo / sin referrer"] += row["total"]

    sources = [
        {
            "label": source,
            "total": total,
            "share": _percent(total, total_visits),
        }
        for source, total in source_counter.most_common(15)
    ]

    channel_totals = {
        "Facebook": 0,
        "Instagram": 0,
        "TikTok": 0,
        "Google": 0,
        "Directo": 0,
        "Otros": 0,
    }
    for source, total in source_counter.items():
        normalized_source = (source or "").lower()
        if "instagram" in normalized_source:
            channel = "Instagram"
        elif "facebook" in normalized_source or normalized_source == "meta":
            channel = "Facebook"
        elif "tiktok" in normalized_source:
            channel = "TikTok"
        elif "google" in normalized_source:
            channel = "Google"
        elif "directo" in normalized_source or "sin referrer" in normalized_source:
            channel = "Directo"
        else:
            channel = "Otros"
        channel_totals[channel] += total

    campaign_channels = [
        {
            "label": label,
            "total": total,
            "share": _percent(total, total_visits),
        }
        for label, total in channel_totals.items()
    ]

    languages = [
        {
            "language": row["language"] or "N/D",
            "total": row["total"],
            "share": _percent(row["total"], total_visits),
        }
        for row in (
            qs_scope
            .values("language")
            .annotate(total=Count("id"))
            .order_by("-total")
        )
    ]

    bot_total = qs_bot_period.count()
    human_total = qs_human_period.count()
    internal_total = qs_internal_period.count()
    bot_pressure = _percent(bot_total, human_total + bot_total)
    commercial_event_types = (
        PublicAnalyticsEvent.EVENT_LANDING_VIEW,
        PublicAnalyticsEvent.EVENT_CTA_CLICK,
        PublicAnalyticsEvent.EVENT_SIGNUP_START,
        PublicAnalyticsEvent.EVENT_SIGNUP_COMPLETE,
        PublicAnalyticsEvent.EVENT_ONBOARDING_COMPLETE,
        PublicAnalyticsEvent.EVENT_SUBSCRIPTION_PAID,
    )
    commercial_events_total = events_all.filter(event_type__in=commercial_event_types).count()

    event_counts = {
        row["event_type"]: row["total"]
        for row in events_all.values("event_type").annotate(total=Count("id"))
    }
    previous_event_counts = {
        row["event_type"]: row["total"]
        for row in previous_events.values("event_type").annotate(total=Count("id"))
    }

    cta_kind_labels = {
        "free_trial_click": "Prueba gratis",
        "whatsapp_click": "WhatsApp",
        "demo_request_click": "Solicitar demostración",
    }
    cta_breakdown = [
        {
            "kind": row["metadata__cta_kind"] or "cta_click",
            "label": cta_kind_labels.get(row["metadata__cta_kind"], "Otro CTA"),
            "total": row["total"],
            "share": _percent(row["total"], event_counts.get(PublicAnalyticsEvent.EVENT_CTA_CLICK, 0)),
        }
        for row in (
            events_all
            .filter(event_type=PublicAnalyticsEvent.EVENT_CTA_CLICK)
            .values("metadata__cta_kind")
            .annotate(total=Count("id"))
            .order_by("-total")
        )
    ]

    device_rows = [
        {
            "label": "Móvil" if row["is_mobile"] else "Desktop",
            "total": row["total"],
            "share": _percent(row["total"], total_visits),
        }
        for row in (
            qs_scope
            .values("is_mobile")
            .annotate(total=Count("id"))
            .order_by("-total")
        )
    ]

    funnel_rows = [
        {
            "key": PublicAnalyticsEvent.EVENT_LANDING_VIEW,
            "label": "Landing comercial registrada",
            "value": event_counts.get(PublicAnalyticsEvent.EVENT_LANDING_VIEW, 0),
            "previous": previous_event_counts.get(PublicAnalyticsEvent.EVENT_LANDING_VIEW, 0),
        },
        {
            "key": PublicAnalyticsEvent.EVENT_CTA_CLICK,
            "label": "Presionaron CTA",
            "value": event_counts.get(PublicAnalyticsEvent.EVENT_CTA_CLICK, 0),
            "previous": previous_event_counts.get(PublicAnalyticsEvent.EVENT_CTA_CLICK, 0),
        },
        {
            "key": PublicAnalyticsEvent.EVENT_SIGNUP_START,
            "label": "Comenzaron registro",
            "value": event_counts.get(PublicAnalyticsEvent.EVENT_SIGNUP_START, 0),
            "previous": previous_event_counts.get(PublicAnalyticsEvent.EVENT_SIGNUP_START, 0),
        },
        {
            "key": PublicAnalyticsEvent.EVENT_SIGNUP_COMPLETE,
            "label": "Completaron registro",
            "value": event_counts.get(PublicAnalyticsEvent.EVENT_SIGNUP_COMPLETE, 0),
            "previous": previous_event_counts.get(PublicAnalyticsEvent.EVENT_SIGNUP_COMPLETE, 0),
        },
        {
            "key": PublicAnalyticsEvent.EVENT_ONBOARDING_COMPLETE,
            "label": "Completaron onboarding",
            "value": event_counts.get(PublicAnalyticsEvent.EVENT_ONBOARDING_COMPLETE, 0),
            "previous": previous_event_counts.get(PublicAnalyticsEvent.EVENT_ONBOARDING_COMPLETE, 0),
        },
        {
            "key": PublicAnalyticsEvent.EVENT_SUBSCRIPTION_PAID,
            "label": "Pagos atribuidos",
            "value": event_counts.get(PublicAnalyticsEvent.EVENT_SUBSCRIPTION_PAID, 0),
            "previous": previous_event_counts.get(PublicAnalyticsEvent.EVENT_SUBSCRIPTION_PAID, 0),
        },
    ]
    baseline = landing_unique_visitors or funnel_rows[0]["value"] or 1
    previous_step = baseline
    for row in funnel_rows:
        row["share"] = _percent(row["value"], baseline)
        row["step_rate"] = _percent(row["value"], previous_step)
        row["delta"] = _percent(row["value"] - row["previous"], row["previous"])
        previous_step = row["value"] or previous_step

    attributed_signup_count = event_counts.get(PublicAnalyticsEvent.EVENT_SIGNUP_COMPLETE, 0)
    attributed_paid_count = event_counts.get(PublicAnalyticsEvent.EVENT_SUBSCRIPTION_PAID, 0)
    unattributed_companies = max(empresas_period.count() - attributed_signup_count, 0)
    unattributed_paid = max(paid_period - attributed_paid_count, 0)

    campaigns = [
        {
            "campaign": row["utm_campaign"] or "Sin campaña",
            "source": row["utm_source"] or "N/D",
            "events": row["events"],
            "signups": row["signups"],
            "paid": row["paid"],
            "signup_rate": _percent(row["signups"], row["events"]),
            "paid_rate": _percent(row["paid"], row["events"]),
        }
        for row in (
            events_all
            .values("utm_campaign", "utm_source")
            .annotate(
                events=Count("id"),
                signups=Count("id", filter=Q(event_type=PublicAnalyticsEvent.EVENT_SIGNUP_COMPLETE)),
                paid=Count("id", filter=Q(event_type=PublicAnalyticsEvent.EVENT_SUBSCRIPTION_PAID)),
            )
            .order_by("-events")[:12]
        )
    ]

    chart_data = {
        "trend": {
            "labels": [
                row["day"].strftime("%d/%m") if row["day"] else "N/D"
                for row in trend_rows
            ],
            "visits": [row["visits"] for row in trend_rows],
            "unique": [row["unique"] for row in trend_rows],
        },
        "countries": {
            "labels": [row["label"] for row in countries[:8]],
            "values": [row["total"] for row in countries[:8]],
        },
        "rubros": {
            "labels": [row["label"] for row in rubros[:8]],
            "values": [row["total"] for row in rubros[:8]],
        },
    }

    top_country = countries[0] if countries else None
    top_rubro = rubros[0] if rubros else None
    top_source = sources[0] if sources else None

    insights = []
    if top_country:
        insights.append(
            f"{top_country['label']} concentra {top_country['share']}% del tráfico filtrado."
        )
    if top_rubro:
        insights.append(
            f"El rubro con mayor intención es {top_rubro['label']} ({top_rubro['total']} visitas)."
        )
    if bot_pressure >= 35:
        insights.append(
            f"Presión alta de bots: {bot_pressure}% del tráfico bruto del período."
        )
    if top_source:
        insights.append(
            f"La fuente principal es {top_source['label']} con {top_source['share']}% de las visitas."
        )
    if unattributed_companies:
        insights.append(
            f"{unattributed_companies} empresa(s) del período no tienen evento de registro atribuido al embudo."
        )
    if not insights:
        insights.append("Aún falta volumen para detectar patrones confiables.")

    quality_warnings = []
    if sessions and visits_per_session >= 20:
        quality_warnings.append(
            f"Promedio anómalo: {visits_per_session} páginas por sesión. Revisar bots, monitores o tráfico técnico."
        )
    if unique_visitors > sessions * 5 and sessions:
        quality_warnings.append(
            f"{unique_visitors} visitantes únicos frente a {sessions} sesiones: la identidad de visitantes está sobredimensionada."
        )
    if _percent(direct_visits, total_visits) >= 80 and total_visits:
        quality_warnings.append(
            f"{_percent(direct_visits, total_visits)}% figura como directo/sin referrer; faltan UTMs o hay tráfico no atribuible."
        )
    if _percent(unknown_language_visits, total_visits) >= 50 and total_visits:
        quality_warnings.append(
            f"{_percent(unknown_language_visits, total_visits)}% no trae idioma detectado; señal típica de solicitudes no comerciales o rutas sin localización."
        )
    if landing_visits and not event_counts.get(PublicAnalyticsEvent.EVENT_CTA_CLICK, 0):
        quality_warnings.append(
            "Hay landings vistas pero cero CTA registrados; revisar enlaces, script de eventos y propuesta de acción."
        )
    if not quality_warnings:
        quality_warnings.append("La muestra filtrada no presenta alertas fuertes de consistencia.")

    context = {
        "days": days,
        "selected_country": selected_country,
        "selected_rubro": selected_rubro,
        "include_bots": include_bots,
        "generated_at": now,
        "since": since,
        "filters": {
            "countries": COUNTRY_LABELS,
            "rubros": RUBRO_LABELS,
        },
        "kpis": {
            "total_visits": total_visits,
            "raw_visits": raw_visits,
            "raw_human_candidate_visits": raw_human_candidate_visits,
            "unique_visitors": unique_visitors,
            "sessions": sessions,
            "mobile_visits": mobile_visits,
            "mobile_share": _percent(mobile_visits, total_visits),
            "landing_visits": landing_visits,
            "landing_unique_visitors": landing_unique_visitors,
            "landing_sessions": landing_sessions,
            "welcome_visits": welcome_visits,
            "home_visits": home_visits,
            "bot_pressure": bot_pressure,
            "trend_delta": trend_delta,
            "new_companies": empresas_period.count(),
            "trials": trials_period,
            "paid": paid_period,
            "attributed_signups": attributed_signup_count,
            "attributed_paid": attributed_paid_count,
            "unattributed_companies": unattributed_companies,
            "unattributed_paid": unattributed_paid,
            "commercial_events_total": commercial_events_total,
            "visit_to_company_rate": _percent(attributed_signup_count, landing_unique_visitors),
            "clean_traffic": human_total,
            "excluded_internal": internal_total,
            "unknown_language_visits": unknown_language_visits,
            "unknown_language_share": _percent(unknown_language_visits, total_visits),
            "direct_visits": direct_visits,
            "direct_share": _percent(direct_visits, total_visits),
            "visits_per_session": visits_per_session,
        },
        "countries": countries,
        "rubros": rubros,
        "country_rubro": country_rubro,
        "page_types": page_type_rows,
        "top_pages": top_pages,
        "entry_pages": entry_pages,
        "sources": sources,
        "campaign_channels": campaign_channels,
        "cta_breakdown": cta_breakdown,
        "device_rows": device_rows,
        "funnel_rows": funnel_rows,
        "campaigns": campaigns,
        "languages": languages,
        "insights": insights,
        "quality_warnings": quality_warnings,
        "chart_data_json": json.dumps(chart_data),
    }

    return TemplateResponse(
        request,
        "admin/visitas/dashboard.html",
        context,
    )


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
