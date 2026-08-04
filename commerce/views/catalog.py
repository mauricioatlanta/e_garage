import datetime
import re

from django.http import Http404, JsonResponse
from django.shortcuts import render

from commerce.services.gateway import CommerceCatalogGateway

# Año → norma Euro (bencina). Referencia: implementación en Chile.
_EURO_NORM = [
    (2015, "cataliticos-twc-euro5", "Euro 5", "Vehículos {year} requieren norma Euro 5."),
    (2007, "cataliticos-twc-euro4", "Euro 4", "Vehículos {year} corresponden a norma Euro 4."),
    (0,    "cataliticos-twc-euro3", "Euro 3", "Vehículos hasta 2006 corresponden a norma Euro 3."),
]

# Cilindrada (cc) → diámetros recomendados de flexible (coinciden con el nombre del producto).
_FLEX_DIAMETERS = [
    (2700, ["3", "4"],       '3" – 4"', "SUV grande, pickup o van"),
    (2000, ["2.5", "2,5", "3"], '2.5" – 3"', "SUV / sedán grande"),
    (1600, ["2", "2.5", "2,5"], '2" – 2.5"', "auto mediano"),
    (1300, ["1.75", "1,75", "2"], '1.75" – 2"', "auto pequeño o city car"),
    (0,    ["1.75", "1,75"],  '1.75"',   "motor pequeño (≤1300 cc)"),
]


def _gateway(request):
    empresa = getattr(request, "empresa", None) or getattr(request, "commerce_empresa", None)
    if not empresa:
        raise Http404
    return CommerceCatalogGateway(empresa)


def _empresa(request):
    return getattr(request, "empresa", None) or getattr(request, "commerce_empresa", None)


def _base_ctx(request, gw):
    root_cats = gw.get_categories()
    return {
        "empresa": _empresa(request),
        "brand": request.commerce_brand,
        "categories": root_cats,
        "root_categories": root_cats,
    }


def _vehicle_ctx(request):
    from commerce.models import CommerceVehicleBrand
    empresa = _empresa(request)
    current_year = datetime.date.today().year
    years = list(range(current_year + 1, 1984, -1))
    brands = list(
        CommerceVehicleBrand.objects.filter(empresa=empresa).values("id", "name")
    ) if empresa else []
    return {"years": years, "brands": brands}


def _safe_category(gw, slug):
    """Devuelve la categoría o None si no existe."""
    try:
        return gw.get_category(slug)
    except Http404:
        return None


def _flex_diameter_from_name(nombre):
    """Extrae el diámetro (float) del nombre de un flexible. Ej: 'Flexible 2.5X6' → 2.5"""
    m = re.search(r'(\d+[.,]\d+|\d+)\s*[Xx×-]', nombre)
    if not m:
        return None
    return float(m.group(1).replace(',', '.'))


def catalog_home(request):
    gw = _gateway(request)
    ctx = _base_ctx(request, gw)
    ctx.update(_vehicle_ctx(request))
    ctx["featured"] = gw.list_products(limit=8)
    brand = ctx.get("brand") or {}
    ctx["title"] = brand.get("meta_title", "")
    ctx["meta_description"] = brand.get("meta_description", "")
    return render(request, "commerce/themes/monteazul/home.html", ctx)


def category_detail(request, slug):
    gw = _gateway(request)
    category = gw.get_category(slug)
    ctx = _base_ctx(request, gw)
    ctx.update({
        "category": category,
        "current_category": category,
        "subcategories": gw.get_categories(parent=category),
        "products": gw.list_products(category=category),
        "q": request.GET.get("q", ""),
        "is_cataliticos_subcat": False,
    })
    return render(request, "commerce/themes/monteazul/catalog/product_list.html", ctx)


def product_detail(request, slug):
    gw = _gateway(request)
    product = gw.get_product(slug)
    ctx = _base_ctx(request, gw)
    ctx.update({
        "product": product,
        "images": product.images.all(),
        "related": (
            gw.list_products(category=product.category, limit=4, exclude_product=product)
            if product.category else []
        ),
    })
    return render(request, "commerce/themes/monteazul/catalog/product_detail.html", ctx)


def search_view(request):
    gw = _gateway(request)
    query = request.GET.get("q", "").strip()
    ctx = _base_ctx(request, gw)
    ctx.update({
        "q": query,
        "products": gw.search(query),
        "current_category": None,
        "is_cataliticos_subcat": False,
    })
    return render(request, "commerce/themes/monteazul/catalog/product_list.html", ctx)


def vehicle_search_view(request):
    """
    Búsqueda por vehículo sin tabla de compatibilidad.
    Usa año+combustible → norma Euro para catalizadores,
    cilindrada → diámetro para flexibles,
    y muestra silenciadores/colas de escape siempre.
    """
    gw = _gateway(request)
    ctx = _base_ctx(request, gw)
    ctx.update(_vehicle_ctx(request))

    raw_year = request.GET.get("year", "").strip()
    fuel = request.GET.get("fuel_type", "").strip().upper()
    raw_cc = request.GET.get("displacement_cc", "").strip()
    brand_name = request.GET.get("brand_name", "").strip()
    model_name = request.GET.get("model_name", "").strip()

    year = int(raw_year) if raw_year.isdigit() else 0
    displacement = int(raw_cc) if raw_cc.isdigit() else 0

    sections = []

    # ── Catalizadores ──────────────────────────────────────────────
    if year and fuel:
        if fuel in ("DIESEL", "DIÉSEL"):
            cat_slug = "cataliticos-twc-diesel"
            cat_label = "Catalizadores Diesel"
            cat_note = "Para motores diésel, cualquier año."
        else:
            for min_year, slug, label, note_tpl in _EURO_NORM:
                if year >= min_year:
                    cat_slug = slug
                    cat_label = f"Catalizadores {label}"
                    cat_note = note_tpl.format(year=year)
                    break

        cat_obj = _safe_category(gw, cat_slug)
        if cat_obj:
            prods = list(gw.list_products(category=cat_obj))
            if prods:
                sections.append({
                    "icon": "⚙️",
                    "label": cat_label,
                    "note": cat_note,
                    "products": prods,
                    "cat_url": f"?cat={cat_slug}",
                })

        # Tipo original (ensamble directo) — solo si el nombre del producto coincide con la marca/modelo buscado
        orig = _safe_category(gw, "cataliticos-tipo-original")
        if orig:
            all_orig = list(gw.list_products(category=orig))
            if brand_name or model_name:
                search_terms = [t.lower() for t in [brand_name, model_name] if t]
                orig_prods = [
                    p for p in all_orig
                    if any(term in p.nombre.lower() for term in search_terms)
                ]
            else:
                orig_prods = all_orig
            if orig_prods:
                sections.append({
                    "icon": "🔩",
                    "label": "Tipo Original (Ensamble Directo)",
                    "note": "Catalizadores plug & play específicos para tu vehículo.",
                    "products": orig_prods,
                    "cat_url": "?cat=cataliticos-tipo-original",
                })

    # ── Flexibles ─────────────────────────────────────────────────
    flex_slugs = ["flexibles-normales", "flexibles-con-extension"]
    for flex_slug in flex_slugs:
        flex_cat = _safe_category(gw, flex_slug)
        if not flex_cat:
            continue
        all_flex = list(gw.list_products(category=flex_cat))
        if not all_flex:
            continue

        if displacement:
            # Determinar diámetros recomendados según cilindrada
            for min_cc, diams, diam_label, vehicle_desc in _FLEX_DIAMETERS:
                if displacement > min_cc:
                    break

            def _matches(p):
                d = _flex_diameter_from_name(p.nombre)
                if d is None:
                    return False
                return any(
                    abs(d - float(target.replace(',', '.'))) < 0.05
                    for target in diams
                    if re.match(r'[\d.,]+$', target)
                )

            filtered = [p for p in all_flex if _matches(p)]
            note = (
                f"Diámetro sugerido {diam_label} para motor de {displacement} cc ({vehicle_desc}). "
                "El diámetro correcto depende de la tubería existente en tu vehículo."
            )
            show = filtered or all_flex  # fallback a todos si el filtro queda vacío
        else:
            show = all_flex
            note = "Todos los diámetros disponibles. Para elegir el correcto mide la tubería de escape de tu vehículo."

        label = "Flexibles Reforzados con Extensión" if flex_slug == "flexibles-con-extension" else "Flexibles Reforzados"
        icon = "🔧"
        sections.append({
            "icon": icon,
            "label": label,
            "note": note,
            "products": show,
            "cat_url": f"?cat={flex_slug}",
        })

    # ── Silenciadores ─────────────────────────────────────────────
    sil_cat = _safe_category(gw, "silenciadores")
    if sil_cat:
        sil_prods = list(gw.list_products(category=sil_cat))
        if sil_prods:
            sections.append({
                "icon": "🔇",
                "label": "Silenciadores de Alto Flujo",
                "note": "Silenciadores deportivos universales de alto rendimiento.",
                "products": sil_prods,
                "cat_url": "?cat=silenciadores",
            })

    # ── Colas / Puntas de escape ──────────────────────────────────
    cola_cat = _safe_category(gw, "colas-de-escape")
    if cola_cat:
        cola_prods = list(gw.list_products(category=cola_cat))
        if cola_prods:
            sections.append({
                "icon": "💨",
                "label": "Puntas y Colas de Escape",
                "note": "Terminaciones decorativas y funcionales. Universales por diámetro.",
                "products": cola_prods,
                "cat_url": "?cat=colas-de-escape",
            })

    vehicle_label_parts = [p for p in [brand_name, model_name, str(year) if year else ""] if p]
    vehicle_label = " ".join(vehicle_label_parts) or "tu vehículo"
    fuel_display = {"DIESEL": "Diésel", "DIÉSEL": "Diésel", "GASOLINA": "Gasolina", "HIBRIDO": "Híbrido", "EV": "Eléctrico"}.get(fuel, fuel)

    ctx.update({
        "year": year,
        "fuel_type": fuel,
        "fuel_display": fuel_display,
        "displacement": displacement,
        "brand_name": brand_name,
        "model_name": model_name,
        "vehicle_label": vehicle_label,
        "sections": sections,
        "has_results": bool(sections),
        "show_vehicle_form": True,
    })
    return render(request, "commerce/themes/monteazul/catalog/vehicle_results.html", ctx)


def api_vehicle_models(request):
    """GET /commerce/api/vehicle-models/?brand_id=<id>  →  {models: [{id, name}, ...]}"""
    from commerce.models import CommerceVehicleModel
    empresa = _empresa(request)
    if not empresa:
        return JsonResponse({"models": []})
    brand_id = request.GET.get("brand_id", "")
    qs = CommerceVehicleModel.objects.filter(empresa=empresa)
    if brand_id:
        qs = qs.filter(brand_id=brand_id)
    models = list(qs.values("id", "name").order_by("name"))
    return JsonResponse({"models": models})
