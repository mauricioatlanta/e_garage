"""
Per-country configuration for Welcome Experience 2.0.
Keys are (country_code, lang) tuples.
"""

_LATAM_RUBRO_CARDS = [
    {"icon": "🔧", "title": "Taller Mecánico", "subtitle": "Órdenes de trabajo, diagnósticos, clientes y vehículos", "rubro": "taller"},
    {"icon": "🚗", "title": "Desarmaduría", "subtitle": "Inventario de piezas, ventas por pieza y trazabilidad", "rubro": "desarmaduría"},
    {"icon": "📦", "title": "Casa de Repuestos", "subtitle": "Catálogo, stock, cotizaciones y control de inventario", "rubro": "repuestos"},
]

_MX_RUBRO_CARDS = [
    {"icon": "🔧", "title": "Taller Mecánico", "subtitle": "Órdenes de trabajo, diagnósticos, clientes y vehículos", "rubro": "taller"},
    {"icon": "🚗", "title": "Deshuesadero / Yonke", "subtitle": "Inventario de piezas, ventas por pieza y trazabilidad", "rubro": "desarmaduría"},
    {"icon": "📦", "title": "Tienda de Refacciones", "subtitle": "Catálogo, stock, cotizaciones y control de inventario", "rubro": "repuestos"},
]

_LATAM_BUSINESS_TYPES = [
    {"icon": "🔧", "title": "Talleres Mecánicos", "body": "Gestión completa de órdenes de servicio, diagnósticos, revisiones y mantenimientos preventivos y correctivos."},
    {"icon": "🚗", "title": "Desarmadurías", "body": "Control de vehículos ingresados, inventario de piezas usadas, ventas por pieza y trazabilidad completa de cada unidad."},
    {"icon": "🛞", "title": "Llanterías y Vulcanización", "body": "Control de llantas, rotación, balanceo, alineación y stock de llantas nuevas y reencauchadas."},
    {"icon": "⚙️", "title": "Tiendas de Repuestos", "body": "Gestión de inventario, ventas, catálogo de repuestos, proveedores y control de entradas y salidas."},
    {"icon": "🔨", "title": "Hojalatería y Carrocería", "body": "Control de reparaciones, abolladuras, soldaduras y restauración de carrocerías y estructuras."},
    {"icon": "🎨", "title": "Pintura y Detallado", "body": "Gestión de servicios de pintura, pulido, vitrificado y acabados especiales."},
    {"icon": "🚗", "title": "Centro Automotriz", "body": "Solución completa para centros que ofrecen múltiples servicios: mecánica, alineación, balanceo y más."},
    {"icon": "⚡", "title": "Suspensión y Amortiguadores", "body": "Especializado en sistemas de suspensión, amortiguadores, resortes y kits de suspensión."},
    {"icon": "🔌", "title": "Eléctrica Automotriz", "body": "Control de servicios eléctricos, inyección electrónica, batería, alternador y sistemas electrónicos."},
]

_MX_BUSINESS_TYPES = [
    {"icon": "🔧", "title": "Talleres Mecánicos", "body": "Gestión completa de órdenes de servicio, diagnósticos, revisiones y mantenimientos preventivos y correctivos."},
    {"icon": "🚗", "title": "Desarmadurías / Yonkes", "body": "Control de vehículos ingresados, inventario de piezas usadas, ventas por pieza y trazabilidad completa de cada unidad."},
    {"icon": "🛞", "title": "Llanterías y Vulcanización", "body": "Control de llantas, rotación, balanceo, alineación y stock de llantas nuevas y reencauchadas."},
    {"icon": "⚙️", "title": "Tiendas de Refacciones", "body": "Gestión de inventario, ventas, catálogo de repuestos, proveedores y control de entradas y salidas."},
    {"icon": "🔨", "title": "Hojalatería y Carrocería", "body": "Control de reparaciones, abolladuras, soldaduras y restauración de carrocerías y estructuras."},
    {"icon": "🎨", "title": "Pintura y Detallado", "body": "Gestión de servicios de pintura, pulido, vitrificado y acabados especiales."},
    {"icon": "🚗", "title": "Centro Automotriz", "body": "Solución completa para centros que ofrecen múltiples servicios: mecánica, alineación, balanceo y más."},
    {"icon": "⚡", "title": "Suspensión y Amortiguadores", "body": "Especializado en sistemas de suspensión, amortiguadores, resortes y kits de suspensión."},
    {"icon": "🚛", "title": "Mecánica Diesel", "body": "Gestión especializada para talleres de vehículos pesados, camiones y motores diesel."},
]

_US_BUSINESS_TYPES = [
    {"icon": "🔧", "title": "Auto Repair Shops", "body": "Complete management of work orders, diagnostics, inspections and preventive and corrective maintenance."},
    {"icon": "🛞", "title": "Tire Shops", "body": "Control of tires, rotation, balancing, alignment and stock of new and retreaded tires."},
    {"icon": "⚙️", "title": "Parts Stores", "body": "Inventory management, sales, parts catalog, suppliers and entry and exit control."},
    {"icon": "🔨", "title": "Body Shops", "body": "Control of repairs, dents, welds and restoration of bodies and structures."},
    {"icon": "🎨", "title": "Paint & Detailing", "body": "Management of painting services, polishing, vitrification and special finishes."},
    {"icon": "🚗", "title": "Salvage Yards", "body": "Vehicle dismantling, part inventory, kiosk, smart pricing and warehouse location tracking."},
    {"icon": "🚗", "title": "Auto Centers", "body": "Complete solution for centers offering multiple services: mechanics, alignment, balancing and more."},
    {"icon": "⚡", "title": "Suspension & Shocks", "body": "Specialized in suspension systems, shocks, springs and suspension kits."},
    {"icon": "🔌", "title": "Automotive Electrical", "body": "Control of electrical services, electronic injection, battery, alternator and electronic systems."},
]

_MOBILE_LOCAL_ES = {"title": "📱 Mobile First", "bullets": ["Interfaz optimizada para móviles", "Funciona sin conexión", "App nativa (próximamente)", "Sincronización automática"]}
_MOBILE_LOCAL_EN = {"title": "📱 Mobile First", "bullets": ["Mobile-optimized interface", "Works offline", "Native app (coming soon)", "Automatic synchronization"]}

# Badge colors for the theme object.
# Most countries: sky blue (#38bdf8) — legible on dark and mid-tone backgrounds.
# Yellow-primary countries (CO, EC, VE): navy (#1e40af) — high contrast on yellow.
_BADGE_SKY = "#38bdf8"
_BADGE_NAVY = "#1e40af"

# Platform-wide stats (eGarage users, not market size).
# These are global — same across all country pages.
# Source: Hero Maestro art direction, 2026-08-05.
PLATFORM_STATS = [
    {"value": "+8,500",  "label": "Talleres en eGarage"},
    {"value": "+2,5M",   "label": "Órdenes de trabajo gestionadas"},
    {"value": "+11",     "label": "Países en Latinoamérica"},
    {"value": "99,5%",   "label": "Disponibilidad de la plataforma"},
]

# Master hero headline and subline — shared base, countries can override.
# Derived from the Hero Maestro visual concept (2026-08-05).
HERO_HEADLINE = "El software de gestión para talleres que quieren crecer, sin complicarse."
HERO_SUBLINE = "Controla tu taller, repuestos, desarmaduría o carwash desde cualquier lugar."

# ─── SPRINT B VISUAL LIBRARY ────────────────────────────────────────────────
#
# Five master assets. These files are shared by ALL country heroes.
# Once approved they never change — only country composition wrappers change.
#
# asset path pattern : static/img/welcome/scenes/{scene}.webp
# country hero path  : static/img/welcome/{country}/hero.webp (Sprint B2)
#
# Every field is actionable for BOTH a human art director and an AI generator.
#   camera      → focal length / lens character
#   lighting    → colour temperature and source direction
#   mood        → emotional register the photo must communicate
#   people      → True = at least one person MUST appear and be the protagonist
#   people_roles → who appears (["técnico"], ["empleado","cliente"], etc.)
#   people_action → one sentence describing exactly what they are doing
#   vehicle     → "elevated" | "engine" | "country" | "none"
#                 "country" means: use the vehicle list from the country config
#   composition → dominant visual weight: "left" | "center" | "right"
#   overlay     → dark overlay for text legibility: "dark" | "medium" | "none"
#   dashboard   → True only for the dashboard master asset

# Dashboard — the 5th master asset. NOT a screenshot of the real ERP.
# A marketing mockup designed to SELL: big KPIs, clean layout, no clutter.
DASHBOARD_SCENE = {
    "scene": "dashboard",
    "label": "Dashboard eGarage",
    "description": "KPIs en tiempo real: ventas, OTs, stock, agenda y clientes.",
    "image": "img/welcome/scenes/dashboard.webp",
    "camera": "50mm",
    "lighting": "studio",
    "mood": "clean",
    "people": False,
    "people_roles": [],
    "people_action": "",
    "vehicle": "none",
    "composition": "center",
    "overlay": "none",
    "dashboard": True,
    "kpis": ["Ventas del mes", "Órdenes de Trabajo", "Stock Crítico", "Agenda", "Clientes activos"],
}

# The four rubro scenes shown in the hero grid (right side, 2×2 card layout).
# Rounded corners 18–24 px, shadow, 20–30 px gap — separation through depth, no borders.
HERO_RUBRO_SCENES = [
    {
        "scene": "taller",
        "rubro": "taller",
        "label": "Taller",
        "description": "Gestiona órdenes, clientes y diagnósticos.",
        "image": "img/welcome/scenes/taller.webp",
        "camera": "35mm",
        "lighting": "warm",
        "mood": "professional",
        "people": True,
        "people_roles": ["técnico", "cliente"],
        "people_action": "Técnico muestra tablet al cliente frente a vehículo elevado en elevador hidráulico. Herramientas ordenadas al fondo.",
        "vehicle": "elevated",
        "composition": "center",
        "overlay": "dark",
        "dashboard": False,
    },
    {
        "scene": "repuestos",
        "rubro": "repuestos",
        "label": "Repuestos",
        "description": "Controla tu inventario y vende más rápido.",
        "image": "img/welcome/scenes/repuestos.webp",
        "camera": "35mm",
        "lighting": "neutral",
        "mood": "organized",
        "people": True,
        "people_roles": ["empleado"],
        "people_action": "Empleado escanea código QR en estantería impecable con cajas etiquetadas. Scanner en mano, postura activa.",
        "vehicle": "none",
        "composition": "right",
        "overlay": "dark",
        "dashboard": False,
    },
    {
        "scene": "desarme",
        "rubro": "desarmaduría",
        "label": "Desarmaduría",
        "description": "Registra piezas y maximiza el valor de cada parte.",
        "image": "img/welcome/scenes/desarme.webp",
        "camera": "35mm",
        "lighting": "warm",
        "mood": "professional",
        "people": True,
        "people_roles": ["operario"],
        "people_action": "Operario etiqueta motor con código QR visible. Tablet en la otra mano. Ambiente ordenado — no un patio, un centro de logística.",
        "vehicle": "engine",
        "composition": "left",
        "overlay": "dark",
        "dashboard": False,
    },
    {
        "scene": "carwash",
        "rubro": "carwash",
        "label": "Carwash",
        "description": "Agenda servicios, control y clientes felices.",
        "image": "img/welcome/scenes/carwash.webp",
        "camera": "35mm",
        "lighting": "bright",
        "mood": "premium",
        "people": True,
        "people_roles": ["empleado", "cliente"],
        "people_action": "Empleado entrega llaves a cliente satisfecho frente a auto brillante con espuma o microfibra visible. Negocio premium, no un lavadero de barrio.",
        "vehicle": "country",
        "composition": "right",
        "overlay": "dark",
        "dashboard": False,
    },
]

# Default art direction for AI image generation (Sprint B+).
# Fields here become the prompt seed for every country; per-country dicts override only what differs.
# "people": True → image MUST include at least one person interacting with the product.
# "dashboard": which marketing mockup version to composite (not the real ERP screenshot).
_DEFAULT_ART_DIRECTION = {
    "lighting": "warm",        # warm | bright | neutral | golden-hour
    "camera": "35mm",          # focal length / lens character
    "mood": "professional",    # professional | energetic | trustworthy
    "environment": "modern",   # modern | industrial | urban-workshop
    "people": True,            # always True — personas are protagonists
    "dashboard": "marketing-v2",
}

# Country-specific overrides. Spread _DEFAULT_ART_DIRECTION first, then override.
_ART_MX = {**_DEFAULT_ART_DIRECTION, "lighting": "warm", "environment": "urban-workshop", "mood": "energetic"}
_ART_PE = {**_DEFAULT_ART_DIRECTION, "lighting": "bright", "environment": "modern"}
_ART_AR = {**_DEFAULT_ART_DIRECTION, "lighting": "warm", "environment": "industrial", "mood": "trustworthy"}
_ART_UY = {**_DEFAULT_ART_DIRECTION, "lighting": "neutral", "environment": "modern", "mood": "professional"}
_ART_VE = {**_DEFAULT_ART_DIRECTION, "lighting": "golden-hour", "environment": "urban-workshop", "mood": "energetic"}
_ART_CO = {**_DEFAULT_ART_DIRECTION, "lighting": "warm", "environment": "urban-workshop", "mood": "energetic"}
_ART_EC = {**_DEFAULT_ART_DIRECTION, "lighting": "bright", "environment": "modern", "mood": "professional"}
_ART_BR = {**_DEFAULT_ART_DIRECTION, "lighting": "warm", "environment": "urban-workshop", "mood": "energetic"}
_ART_US = {**_DEFAULT_ART_DIRECTION, "lighting": "neutral", "environment": "modern", "mood": "professional", "camera": "50mm"}

_LATAM_PLAN_FEATURES = {
    "entry": ["Vehículos ilimitados", "Kiosko automático", "Ubicación Bodega-Estante", "Precio inteligente", "Soporte por WhatsApp"],
    "growth": ["Todo de Entry", "Análisis avanzados", "Multi-sucursales", "Prioridad en soporte"],
    "business": ["Todo de Growth", "Capacitación incluida", "API personalizada", "Soporte dedicado"],
}

_US_PLAN_FEATURES = {
    "entry": ["Unlimited vehicles", "Client portal", "Inventory", "24/7 support"],
    "growth": ["Everything from monthly plan", "Advanced analytics", "Multi-locations", "Priority support"],
    "business": ["Everything from semi-annual plan", "Training included", "Custom API", "Dedicated support"],
}

_LATAM_COMMON_ES = {
    "rubro_label": "¿Qué tipo de negocio tienes?",
    "rubro_extra": "También: vulcanizaciones, car wash, hojalatería y más...",
    "features_title": "Funcionalidades Potentes",
    "business_types_title": "Hecho para Todos los Negocios Automotrices",
    "business_types_subtitle": "No importa el tipo de servicio automotriz, eGarage es perfecto para ti",
    "more_title": "¡Y mucho más!",
    "more_body": "Sea cual sea tu negocio en el sector automotriz, eGarage se adapta a tus necesidades específicas.",
    "cta_login": "🔐 Ya tengo cuenta",
    "cta_precios": "💰 Ver Planes",
    "cta_start": "🚀 Prueba Gratis",
    "popular_badge": "🏆 MÁS POPULAR",
    "plan_select": "Seleccionar",
    "trial_title": "🎁 Prueba Gratis por 30 Días",
    "trial_text": "Sin tarjeta. Sin compromiso. Cancela cuando quieras.",
    "pricing_title": "Planes Accesibles",
    "pricing_subtitle": "Elige el plan que mejor se adapte a tu negocio",
    "rubro_cards": _LATAM_RUBRO_CARDS,
    "business_types": _LATAM_BUSINESS_TYPES,
    "lang_switcher": None,
}

WELCOME_CONFIG = {
    ("mx", "es"): {
        **_LATAM_COMMON_ES,
        "html_lang": "es-mx",
        "country_name": "México",
        "country_code": "mx",
        "flag": "🇲🇽",
        "c1_rgb": "0, 104, 71",
        "c2_rgb": "206, 17, 38",
        "c1_hex": "#006847",
        "c2_hex": "#CE1122",
        "btn_text_color": "#ffffff",
        "hero_subtitle": "El software de gestión para talleres, deshuesaderos y refaccionarias en CDMX, Guadalajara y Monterrey",
        "hero_image": "img/welcome/mx/hero.webp",
        "terminology": [
            {"label": "Vehículo", "value": "Auto Seminuevo"},
            {"label": "Documento", "value": "Factura Original"},
            {"label": "Impuesto", "value": "Tenencia / Refrendo"},
        ],
        "rubro_cards": _MX_RUBRO_CARDS,
        "rubro_extra": "También: llanterías, hojalatería, car wash y más...",
        "features": [
            {"icon": "✅", "title": "Conformidad Fiscal México", "body": "IVA 16% calculado automáticamente. Documentos fiscales para México: facturas, notas de venta y recibos CFDI."},
            {"icon": "📱", "title": "Kiosko Automático", "body": "Guarda patente/modelo/costo y tu tienda online se crea sola con fotos, precio sugerido y ubicación Bodega/Estante."},
            {"icon": "💬", "title": "Venta por WhatsApp", "body": "Link personal para mandar por WhatsApp con stock real y ubicación Bodega/Estante."},
        ],
        "features_footer": "En México: deshuesadero · yonke · taller mecánico · llantería · tienda de refacciones",
        "business_types": _MX_BUSINESS_TYPES,
        "signup_url": "/mx/signup/",
        "login_url": "/mx/login/",
        "precios_url": "/mx/precios/",
        "country_local": {
            "title": "Hecho para México 🇲🇽",
            "subtitle": "Entendemos las necesidades específicas de los talleres mexicanos",
            "items": [
                {"title": "✅ Conformidad Fiscal", "bullets": ["Cálculo automático de IVA (16%)", "Facturación electrónica CFDI", "Control de impuestos", "Integración con contabilidad"]},
                _MOBILE_LOCAL_ES,
                {"title": "💳 Pagos Locales", "bullets": ["Pago móvil integrado", "Transferencias bancarias SPEI", "Tarjetas de crédito/débito", "Moneda local (MXN)"]},
            ],
        },
        "plans": [
            {"name": "Entry", "price": "$370", "period": "MXN por mes", "period_equiv": "≈ $21 USD / mes", "savings": None, "popular": False,
             "features": _LATAM_PLAN_FEATURES["entry"], "url": "/mx/signup/?plan=entry"},
            {"name": "Growth", "price": "$2,035", "period": "MXN por 6 meses", "period_equiv": "≈ $118 USD / 6 meses", "savings": "Ahorra 17%", "popular": True,
             "features": _LATAM_PLAN_FEATURES["growth"], "url": "/mx/signup/?plan=growth"},
            {"name": "Business", "price": "$3,700", "period": "MXN por año", "period_equiv": "≈ $215 USD / año", "savings": "Ahorra 17%", "popular": False,
             "features": _LATAM_PLAN_FEATURES["business"], "url": "/mx/signup/?plan=business"},
        ],
        "meta_title": "eGarage México — Software para Talleres, Yonkes y Refaccionarias",
        "meta_description": "Software de gestión automotriz para talleres mecánicos, deshuesaderos/yonkes y tiendas de refacciones en CDMX, Guadalajara y Monterrey. Prueba gratis 30 días.",
        "og_image": "img/welcome/mx/og.png",
        "theme": {"primary": "#006847", "accent": "#CE1122", "badge": _BADGE_SKY},
        "art_direction": _ART_MX,
        "cities": ["CDMX", "Guadalajara", "Monterrey", "Puebla", "Tijuana"],
        "vehicles": ["NP300", "Aveo", "Jetta", "Hilux", "Tracker"],
        "priority_rubro": "desarmaduría",
        "market_insight": {
            "headline": "Más de 180,000 talleres mecánicos y yonkes operan en México.",
            "tip": "El control de refacciones y la facturación CFDI son los principales desafíos del rubro.",
            "focus": "Con eGarage digitalizas tu taller o yonke desde el primer día, sin complicaciones.",
        },
        "social_proof": {"stats": [
            {"value": "180K+", "label": "talleres en México"},
            {"value": "IVA 16%", "label": "calculado automático"},
            {"value": "30 días", "label": "prueba gratuita"},
        ]},
    },

    ("pe", "es"): {
        **_LATAM_COMMON_ES,
        "html_lang": "es-pe",
        "country_name": "Perú",
        "country_code": "pe",
        "flag": "🇵🇪",
        "c1_rgb": "220, 20, 60",
        "c2_rgb": "180, 0, 30",
        "c1_hex": "#DC143C",
        "c2_hex": "#B4001E",
        "btn_text_color": "#ffffff",
        "hero_subtitle": "Software de gestión para talleres mecánicos, desarmadurías y casas de repuestos en Lima y Arequipa",
        "hero_image": "img/welcome/pe/hero.webp",
        "terminology": [
            {"label": "Vehículo", "value": "Auto Seminuevo"},
            {"label": "Documento", "value": "Tarjeta de Propiedad"},
            {"label": "Impuesto", "value": "Impuesto Vehicular SAT"},
        ],
        "rubro_extra": "También: llanterías, latonería, car wash y más...",
        "features": [
            {"icon": "✅", "title": "Conformidad Fiscal Perú", "body": "IGV 18% calculado automáticamente. Documentos fiscales válidos: facturas, boletas y notas de venta."},
            {"icon": "📱", "title": "Kiosko Automático", "body": "Guarda patente/modelo/costo y tu tienda online se crea sola con fotos, precio sugerido y ubicación Bodega/Estante."},
            {"icon": "💬", "title": "Venta por WhatsApp", "body": "Link personal para mandar por WhatsApp con stock real y ubicación Bodega/Estante."},
        ],
        "features_footer": "En Perú: desarmaduría · taller mecánico · casa de repuestos",
        "signup_url": "/pe/signup/",
        "login_url": "/pe/login/",
        "precios_url": "/pe/precios/",
        "country_local": {
            "title": "Hecho para Perú 🇵🇪",
            "subtitle": "Entendemos las necesidades específicas de los talleres peruanos",
            "items": [
                {"title": "✅ Conformidad Fiscal", "bullets": ["Cálculo automático de IGV (18%)", "Facturas electrónicas", "Control de impuestos", "Integración con contabilidad"]},
                _MOBILE_LOCAL_ES,
                {"title": "💳 Pagos Locales", "bullets": ["Pago móvil integrado", "Transferencias bancarias", "Tarjetas de crédito/débito", "Moneda local (S/)"]},
            ],
        },
        "plans": [
            {"name": "Entry", "price": "S/ 70", "period": "por mes", "period_equiv": None, "savings": None, "popular": False,
             "features": _LATAM_PLAN_FEATURES["entry"], "url": "/pe/signup/?plan=entry"},
            {"name": "Growth", "price": "S/ 350", "period": "por 6 meses", "period_equiv": None, "savings": "Ahorra 17%", "popular": True,
             "features": _LATAM_PLAN_FEATURES["growth"], "url": "/pe/signup/?plan=growth"},
            {"name": "Business", "price": "S/ 700", "period": "por año", "period_equiv": None, "savings": "Ahorra 33%", "popular": False,
             "features": _LATAM_PLAN_FEATURES["business"], "url": "/pe/signup/?plan=business"},
        ],
        "meta_title": "eGarage Perú — Software para Talleres en Lima y Arequipa",
        "meta_description": "Software de gestión para talleres mecánicos, desarmadurías y casas de repuestos en Lima y Arequipa. IGV 18% automático y Sunarp. Prueba gratis 30 días.",
        "og_image": "img/welcome/pe/og.png",
        "theme": {"primary": "#DC143C", "accent": "#B4001E", "badge": _BADGE_SKY},
        "art_direction": _ART_PE,
        "cities": ["Lima", "Arequipa", "Trujillo", "Piura", "Cusco"],
        "vehicles": ["Hilux", "Yaris", "Corolla", "Rush", "Avanza"],
        "priority_rubro": "taller",
        "market_insight": {
            "headline": "Más de 35,000 talleres mecánicos y desarmadurías operan en el Perú.",
            "tip": "El control de GNV/GLP, la Tarjeta de Propiedad y la facturación electrónica Sunat son las claves del rubro.",
            "focus": "Con eGarage automatizas tu taller y cumples con las exigencias del mercado peruano desde el primer día.",
        },
        "social_proof": {"stats": [
            {"value": "35K+", "label": "talleres en Perú"},
            {"value": "IGV 18%", "label": "calculado automático"},
            {"value": "30 días", "label": "prueba gratuita"},
        ]},
    },

    ("ar", "es"): {
        **_LATAM_COMMON_ES,
        "html_lang": "es-ar",
        "country_name": "Argentina",
        "country_code": "ar",
        "flag": "🇦🇷",
        "c1_rgb": "108, 172, 228",
        "c2_rgb": "252, 221, 9",
        "c1_hex": "#6CACE4",
        "c2_hex": "#FCDD09",
        "btn_text_color": "#000000",
        "hero_subtitle": "Gestión digital para talleres mecánicos, desarmadurías y casas de repuestos en CABA, Córdoba y Rosario",
        "hero_image": "img/welcome/ar/hero.webp",
        "terminology": [
            {"label": "Vehículo", "value": "Auto Usado"},
            {"label": "Impuesto", "value": "Patente / VTV"},
            {"label": "Trámite", "value": "08 Firmado"},
        ],
        "rubro_extra": "También: vulcanizaciones, car wash, hojalatería y más...",
        "features": [
            {"icon": "✅", "title": "Conformidad Fiscal Argentina", "body": "IVA 21% calculado automáticamente. Facturas electrónicas AFIP, notas de crédito y débito."},
            {"icon": "📱", "title": "Kiosko Automático", "body": "Guardá patente/modelo/costo y tu tienda online se crea sola con fotos, precio sugerido y ubicación Bodega/Estante."},
            {"icon": "💬", "title": "Venta por WhatsApp", "body": "Link personal para mandar por WhatsApp con stock real y ubicación Bodega/Estante."},
        ],
        "features_footer": "En Argentina: desarmaduría · taller mecánico · casa de repuestos",
        "signup_url": "/ar/signup/",
        "login_url": "/ar/login/",
        "precios_url": "/ar/precios/",
        "country_local": {
            "title": "Hecho para Argentina 🇦🇷",
            "subtitle": "Entendemos las necesidades específicas de los talleres argentinos",
            "items": [
                {"title": "✅ Conformidad Fiscal", "bullets": ["IVA 21% automático", "Facturación electrónica AFIP", "Control de impuestos", "CUIT integrado"]},
                _MOBILE_LOCAL_ES,
                {"title": "💳 Pagos Locales", "bullets": ["Transferencias bancarias CBU", "Tarjetas de crédito/débito", "MercadoPago integrado", "Moneda local (ARS)"]},
            ],
        },
        "plans": [
            {"name": "Entry", "price": "$4.000", "period": "ARS por mes", "period_equiv": "≈ $4 USD / mes", "savings": None, "popular": False,
             "features": _LATAM_PLAN_FEATURES["entry"], "url": "/ar/signup/?plan=entry"},
            {"name": "Growth", "price": "$22.000", "period": "ARS por 6 meses", "period_equiv": "≈ $22 USD / 6 meses", "savings": "Ahorrá 17%", "popular": True,
             "features": _LATAM_PLAN_FEATURES["growth"], "url": "/ar/signup/?plan=growth"},
            {"name": "Business", "price": "$40.000", "period": "ARS por año", "period_equiv": "≈ $40 USD / año", "savings": "Ahorrá 33%", "popular": False,
             "features": _LATAM_PLAN_FEATURES["business"], "url": "/ar/signup/?plan=business"},
        ],
        "meta_title": "eGarage Argentina — Software para Talleres en CABA, Córdoba y Rosario",
        "meta_description": "Software de gestión automotriz para talleres mecánicos, desarmadurías y casas de repuestos en Argentina. Facturación AFIP integrada. Probá gratis 30 días.",
        "og_image": "img/welcome/ar/og.png",
        "theme": {"primary": "#6CACE4", "accent": "#FCDD09", "badge": _BADGE_SKY},
        "art_direction": _ART_AR,
        "cities": ["Buenos Aires", "Córdoba", "Rosario", "Mendoza", "La Plata"],
        "vehicles": ["Cronos", "Hilux", "Oroch", "Volkswagen Gol", "Chevrolet S10"],
        "priority_rubro": "desarmaduría",
        "market_insight": {
            "headline": "Más de 60,000 talleres mecánicos y desarmadurías operan en Argentina.",
            "tip": "La facturación AFIP, el VTV y la gestión del 08 firmado son los pilares del rubro.",
            "focus": "Con eGarage gestionás tu taller con herramientas hechas para el mercado argentino.",
        },
        "social_proof": {"stats": [
            {"value": "60K+", "label": "talleres en Argentina"},
            {"value": "IVA 21%", "label": "calculado automático"},
            {"value": "30 días", "label": "prueba gratuita"},
        ]},
    },

    ("uy", "es"): {
        **_LATAM_COMMON_ES,
        "html_lang": "es-uy",
        "country_name": "Uruguay",
        "country_code": "uy",
        "flag": "🇺🇾",
        "c1_rgb": "0, 56, 168",
        "c2_rgb": "252, 221, 9",
        "c1_hex": "#0038A8",
        "c2_hex": "#FCDD09",
        "btn_text_color": "#ffffff",
        "hero_subtitle": "Gestión digital para talleres mecánicos, desarmadurías y casas de repuestos en Montevideo y Punta del Este",
        "hero_image": "img/welcome/uy/hero.webp",
        "terminology": [
            {"label": "Vehículo", "value": "Auto Usado"},
            {"label": "Documento", "value": "Libreta de Propiedad"},
            {"label": "Impuesto", "value": "Patente SUCIVE"},
        ],
        "rubro_extra": "También: vulcanizaciones, car wash, hojalatería y más...",
        "features": [
            {"icon": "✅", "title": "Conformidad Fiscal Uruguay", "body": "IVA 22% calculado automáticamente. Facturas electrónicas DGI, comprobantes y notas de crédito."},
            {"icon": "📱", "title": "Kiosko Automático", "body": "Guardá matrícula/modelo/costo y tu tienda online se crea sola con fotos, precio sugerido y ubicación Bodega/Estante."},
            {"icon": "💬", "title": "Venta por WhatsApp", "body": "Link personal para mandar por WhatsApp con stock real y ubicación Bodega/Estante."},
        ],
        "features_footer": "En Uruguay: desarmaduría · taller mecánico · casa de repuestos",
        "signup_url": "/uy/signup/",
        "login_url": "/uy/login/",
        "precios_url": "/uy/precios/",
        "country_local": {
            "title": "Hecho para Uruguay 🇺🇾",
            "subtitle": "Entendemos las necesidades específicas de los talleres uruguayos",
            "items": [
                {"title": "✅ Conformidad Fiscal", "bullets": ["IVA 22% automático", "Comprobantes electrónicos DGI", "Control de impuestos", "RUT (Uruguay) integrado"]},
                _MOBILE_LOCAL_ES,
                {"title": "💳 Pagos Locales", "bullets": ["Transferencias bancarias", "Tarjetas de crédito/débito", "Redpagos", "Moneda local (UYU)"]},
            ],
        },
        "plans": [
            {"name": "Entry", "price": "$800", "period": "UYU por mes", "period_equiv": "≈ $20 USD / mes", "savings": None, "popular": False,
             "features": _LATAM_PLAN_FEATURES["entry"], "url": "/uy/signup/?plan=entry"},
            {"name": "Growth", "price": "$4.400", "period": "UYU por 6 meses", "period_equiv": "≈ $110 USD / 6 meses", "savings": "Ahorrá 17%", "popular": True,
             "features": _LATAM_PLAN_FEATURES["growth"], "url": "/uy/signup/?plan=growth"},
            {"name": "Business", "price": "$8.000", "period": "UYU por año", "period_equiv": "≈ $200 USD / año", "savings": "Ahorrá 33%", "popular": False,
             "features": _LATAM_PLAN_FEATURES["business"], "url": "/uy/signup/?plan=business"},
        ],
        "meta_title": "eGarage Uruguay — Software para Talleres en Montevideo",
        "meta_description": "Software de gestión para talleres mecánicos, desarmadurías y casas de repuestos en Uruguay. Facturación DGI y SUCIVE. Probá gratis 30 días.",
        "og_image": "img/welcome/uy/og.png",
        "theme": {"primary": "#0038A8", "accent": "#FCDD09", "badge": _BADGE_SKY},
        "art_direction": _ART_UY,
        "cities": ["Montevideo", "Salto", "Paysandú", "Maldonado", "Punta del Este"],
        "vehicles": ["Hilux", "Gol Trend", "Cronos", "Sandero", "Clio"],
        "priority_rubro": "taller",
        "market_insight": {
            "headline": "Más de 8,000 talleres mecánicos y desarmadurías operan en Uruguay.",
            "tip": "El SUCIVE, la libreta de propiedad y la facturación DGI son las claves del rubro uruguayo.",
            "focus": "Con eGarage gestionás tu taller con cumplimiento fiscal DGI desde el día uno.",
        },
        "social_proof": {"stats": [
            {"value": "8K+", "label": "talleres en Uruguay"},
            {"value": "IVA 22%", "label": "calculado automático"},
            {"value": "30 días", "label": "prueba gratuita"},
        ]},
    },

    ("ve", "es"): {
        **_LATAM_COMMON_ES,
        "html_lang": "es-ve",
        "country_name": "Venezuela",
        "country_code": "ve",
        "flag": "🇻🇪",
        "c1_rgb": "255, 204, 0",
        "c2_rgb": "207, 20, 43",
        "c1_hex": "#FFCC00",
        "c2_hex": "#CF142B",
        "btn_text_color": "#000000",
        "hero_subtitle": "Gestión digital para talleres mecánicos, desarmadurías y casas de repuestos en Caracas y Valencia",
        "hero_image": "img/welcome/ve/hero.webp",
        "terminology": [
            {"label": "Vehículo", "value": "Carro Usado"},
            {"label": "Documento", "value": "Título de Propiedad"},
            {"label": "Trámite", "value": "Experticia INTT"},
        ],
        "rubro_extra": "También: vulcanizaciones, car wash, hojalatería y más...",
        "features": [
            {"icon": "✅", "title": "Documentos Digitales", "body": "Facturas, notas de venta, órdenes de trabajo. Control de impuestos local con soporte multimoneda (USD/Bs)."},
            {"icon": "📱", "title": "Kiosko Automático", "body": "Crea tu tienda online automáticamente con fotos, precio sugerido y ubicación Bodega/Estante."},
            {"icon": "💬", "title": "Venta por WhatsApp", "body": "Link personal para mandar por WhatsApp con stock real y ubicación Bodega/Estante."},
        ],
        "features_footer": "En Venezuela: desarmaduría · taller mecánico · casa de repuestos",
        "signup_url": "/ve/signup/",
        "login_url": "/ve/login/",
        "precios_url": "/ve/precios/",
        "country_local": {
            "title": "Hecho para Venezuela 🇻🇪",
            "subtitle": "Entendemos las necesidades específicas del sector automotriz venezolano",
            "items": [
                {"title": "✅ Multimoneda", "bullets": ["Soporte USD y Bolívares", "Tasas de cambio actualizables", "Documentos en USD o VES", "Control de inventario valorizado"]},
                _MOBILE_LOCAL_ES,
                {"title": "💳 Pagos Locales", "bullets": ["Transferencias bancarias", "Pago móvil", "Zelle / PayPal", "Moneda configurable"]},
            ],
        },
        "plans": [
            {"name": "Entry", "price": "$20", "period": "USD por mes", "period_equiv": None, "savings": None, "popular": False,
             "features": _LATAM_PLAN_FEATURES["entry"], "url": "/ve/signup/?plan=entry"},
            {"name": "Growth", "price": "$110", "period": "USD por 6 meses", "period_equiv": None, "savings": "Ahorra 17%", "popular": True,
             "features": _LATAM_PLAN_FEATURES["growth"], "url": "/ve/signup/?plan=growth"},
            {"name": "Business", "price": "$200", "period": "USD por año", "period_equiv": None, "savings": "Ahorra 33%", "popular": False,
             "features": _LATAM_PLAN_FEATURES["business"], "url": "/ve/signup/?plan=business"},
        ],
        "meta_title": "eGarage Venezuela — Software para Talleres en Caracas y Valencia",
        "meta_description": "Software de gestión para talleres mecánicos, desarmadurías y casas de repuestos en Venezuela. Soporte multimoneda USD/Bs. Prueba gratis 30 días.",
        "og_image": "img/welcome/ve/og.png",
        "theme": {"primary": "#FFCC00", "accent": "#CF142B", "badge": _BADGE_NAVY},
        "art_direction": _ART_VE,
        "cities": ["Caracas", "Valencia", "Maracaibo", "Barquisimeto", "Maturín"],
        "vehicles": ["Chevrolet Spark", "Aveo", "Corolla", "Cruze", "Hilux"],
        "priority_rubro": "taller",
        "market_insight": {
            "headline": "Más de 25,000 talleres mecánicos y desarmadurías operan en Venezuela.",
            "tip": "El soporte multimoneda USD/Bs, la experticia INTT y el control de inventario son los desafíos clave.",
            "focus": "Con eGarage gestionas tu taller con soporte USD/Bs y control total desde el primer día.",
        },
        "social_proof": {"stats": [
            {"value": "25K+", "label": "talleres en Venezuela"},
            {"value": "USD / Bs", "label": "multimoneda"},
            {"value": "30 días", "label": "prueba gratuita"},
        ]},
    },

    ("co", "es"): {
        **_LATAM_COMMON_ES,
        "html_lang": "es-co",
        "country_name": "Colombia",
        "country_code": "co",
        "flag": "🇨🇴",
        "c1_rgb": "252, 209, 22",
        "c2_rgb": "206, 17, 38",
        "c1_hex": "#FCD116",
        "c2_hex": "#CE1122",
        "btn_text_color": "#000000",
        "hero_subtitle": "Gestión digital para talleres mecánicos, chatarrerías y almacenes de repuestos en Bogotá, Medellín y Cali",
        "hero_image": "img/welcome/co/hero.webp",
        "terminology": [
            {"label": "Vehículo", "value": "Carro Usado"},
            {"label": "Seguro", "value": "SOAT Vigente"},
            {"label": "Revisión", "value": "Tecnomecánica"},
        ],
        "rubro_extra": "También: latonería, pintura, car wash y más...",
        "features": [
            {"icon": "✅", "title": "Conformidad Fiscal Colombia", "body": "IVA 19% calculado automáticamente. Facturación electrónica DIAN, notas de venta y recibos."},
            {"icon": "📱", "title": "Kiosko Automático", "body": "Crea tu tienda online automáticamente con fotos, precio sugerido y ubicación Bodega/Estante."},
            {"icon": "💬", "title": "Venta por WhatsApp", "body": "Link personal para mandar por WhatsApp con stock real y ubicación Bodega/Estante."},
        ],
        "features_footer": "En Colombia: chatarrería · taller mecánico · almacén de repuestos",
        "signup_url": "/co/signup/",
        "login_url": "/co/login/",
        "precios_url": "/co/precios/",
        "country_local": {
            "title": "Hecho para Colombia 🇨🇴",
            "subtitle": "Entendemos las necesidades específicas de los talleres colombianos",
            "items": [
                {"title": "✅ Conformidad Fiscal", "bullets": ["IVA 19% automático", "Facturación electrónica DIAN", "Control de impuestos", "NIT integrado"]},
                _MOBILE_LOCAL_ES,
                {"title": "💳 Pagos Locales", "bullets": ["Transferencias bancarias", "Nequi / Daviplata", "Tarjetas de crédito/débito", "Moneda local (COP)"]},
            ],
        },
        "plans": [
            {"name": "Entry", "price": "$90.000", "period": "COP por mes", "period_equiv": "≈ $22 USD / mes", "savings": None, "popular": False,
             "features": _LATAM_PLAN_FEATURES["entry"], "url": "/co/signup/?plan=entry"},
            {"name": "Growth", "price": "$495.000", "period": "COP por 6 meses", "period_equiv": "≈ $120 USD / 6 meses", "savings": "Ahorra 17%", "popular": True,
             "features": _LATAM_PLAN_FEATURES["growth"], "url": "/co/signup/?plan=growth"},
            {"name": "Business", "price": "$900.000", "period": "COP por año", "period_equiv": "≈ $220 USD / año", "savings": "Ahorra 33%", "popular": False,
             "features": _LATAM_PLAN_FEATURES["business"], "url": "/co/signup/?plan=business"},
        ],
        "meta_title": "eGarage Colombia — Software para Talleres en Bogotá, Medellín y Cali",
        "meta_description": "Software de gestión para talleres mecánicos, chatarrerías y almacenes de repuestos en Colombia. Facturación DIAN integrada. Prueba gratis 30 días.",
        "og_image": "img/welcome/co/og.png",
        "theme": {"primary": "#FCD116", "accent": "#CE1122", "badge": _BADGE_NAVY},
        "art_direction": _ART_CO,
        "cities": ["Bogotá", "Medellín", "Cali", "Barranquilla", "Cartagena"],
        "vehicles": ["Spark", "Logan", "Aveo", "Hilux", "NP300"],
        "priority_rubro": "taller",
        "market_insight": {
            "headline": "Más de 50,000 talleres mecánicos y chatarrerías operan en Colombia.",
            "tip": "La facturación DIAN, el SOAT vigente y la tecnomecánica son las claves del rubro colombiano.",
            "focus": "Con eGarage digitalizas tu taller con cumplimiento DIAN y control total desde el primer día.",
        },
        "social_proof": {"stats": [
            {"value": "50K+", "label": "talleres en Colombia"},
            {"value": "IVA 19%", "label": "calculado automático"},
            {"value": "30 días", "label": "prueba gratuita"},
        ]},
    },

    ("ec", "es"): {
        **_LATAM_COMMON_ES,
        "html_lang": "es-ec",
        "country_name": "Ecuador",
        "country_code": "ec",
        "flag": "🇪🇨",
        "c1_rgb": "255, 221, 0",
        "c2_rgb": "239, 51, 64",
        "c1_hex": "#FFDD00",
        "c2_hex": "#EF3340",
        "btn_text_color": "#000000",
        "hero_subtitle": "Gestión digital para talleres mecánicos, desarmadurías y almacenes de repuestos en Quito y Guayaquil",
        "hero_image": "img/welcome/ec/hero.webp",
        "terminology": [
            {"label": "Vehículo", "value": "Auto Seminuevo"},
            {"label": "Matrícula", "value": "Matrícula al día"},
            {"label": "Revisión", "value": "Revisión Vehicular ATM"},
        ],
        "rubro_extra": "También: vulcanizaciones, car wash, enderezada y pintura y más...",
        "features": [
            {"icon": "✅", "title": "Conformidad Fiscal Ecuador", "body": "IVA 12% calculado automáticamente. Comprobantes electrónicos SRI, facturas y notas de venta."},
            {"icon": "📱", "title": "Kiosko Automático", "body": "Crea tu tienda online automáticamente con fotos, precio sugerido y ubicación Bodega/Estante."},
            {"icon": "💬", "title": "Venta por WhatsApp", "body": "Link personal para mandar por WhatsApp con stock real y ubicación Bodega/Estante."},
        ],
        "features_footer": "En Ecuador: chatarrería · taller mecánico · almacén de repuestos",
        "signup_url": "/ec/signup/",
        "login_url": "/ec/login/",
        "precios_url": "/ec/precios/",
        "country_local": {
            "title": "Hecho para Ecuador 🇪🇨",
            "subtitle": "Entendemos las necesidades específicas del sector automotriz ecuatoriano",
            "items": [
                {"title": "✅ Conformidad Fiscal", "bullets": ["IVA 12% automático", "Comprobantes electrónicos SRI", "Control de impuestos", "RUC integrado"]},
                _MOBILE_LOCAL_ES,
                {"title": "💳 Pagos Locales", "bullets": ["Transferencias bancarias", "Tarjetas de crédito/débito", "Moneda local (USD)", "Integración PayPal"]},
            ],
        },
        "plans": [
            {"name": "Entry", "price": "$20", "period": "USD por mes", "period_equiv": None, "savings": None, "popular": False,
             "features": _LATAM_PLAN_FEATURES["entry"], "url": "/ec/signup/?plan=entry"},
            {"name": "Growth", "price": "$110", "period": "USD por 6 meses", "period_equiv": None, "savings": "Ahorra 17%", "popular": True,
             "features": _LATAM_PLAN_FEATURES["growth"], "url": "/ec/signup/?plan=growth"},
            {"name": "Business", "price": "$200", "period": "USD por año", "period_equiv": None, "savings": "Ahorra 33%", "popular": False,
             "features": _LATAM_PLAN_FEATURES["business"], "url": "/ec/signup/?plan=business"},
        ],
        "meta_title": "eGarage Ecuador — Software para Talleres en Quito y Guayaquil",
        "meta_description": "Software de gestión para talleres mecánicos, desarmadurías y almacenes de repuestos en Quito y Guayaquil. Comprobantes SRI integrados. Prueba gratis 30 días.",
        "og_image": "img/welcome/ec/og.png",
        "theme": {"primary": "#FFDD00", "accent": "#EF3340", "badge": _BADGE_NAVY},
        "art_direction": _ART_EC,
        "cities": ["Quito", "Guayaquil", "Cuenca", "Ambato", "Manta"],
        "vehicles": ["Hilux", "D-Max", "Aveo", "Tucson", "Sail"],
        "priority_rubro": "taller",
        "market_insight": {
            "headline": "Más de 15,000 talleres mecánicos y desarmadurías operan en Ecuador.",
            "tip": "La revisión vehicular ATM, la matrícula al día y los comprobantes SRI son los pilares del rubro.",
            "focus": "Con eGarage gestionas tu taller con cumplimiento SRI y control de inventario desde el inicio.",
        },
        "social_proof": {"stats": [
            {"value": "15K+", "label": "talleres en Ecuador"},
            {"value": "IVA 12%", "label": "calculado automático"},
            {"value": "30 días", "label": "prueba gratuita"},
        ]},
    },

    ("br", "es"): {
        **_LATAM_COMMON_ES,
        "html_lang": "es-br",
        "country_name": "Brasil",
        "country_code": "br",
        "flag": "🇧🇷",
        "c1_rgb": "0, 156, 59",
        "c2_rgb": "254, 223, 0",
        "c1_hex": "#009C3B",
        "c2_hex": "#FEDF00",
        "btn_text_color": "#000000",
        "hero_subtitle": "Software de gestión para oficinas mecânicas, desmanches e lojas de autopeças en São Paulo, Rio y Curitiba",
        "hero_image": "img/welcome/br/hero.webp",
        "terminology": [
            {"label": "Veículo", "value": "Carro Usado"},
            {"label": "Documento", "value": "DUT / CRLV"},
            {"label": "Imposto", "value": "IPVA / ICMS"},
        ],
        "rubro_extra": "También: vulcanizaciones, car wash, latonería y más...",
        "features": [
            {"icon": "✅", "title": "Conformidad Fiscal Brasil", "body": "IPI/ICMS/ISS gestionados. NF-e (Nota Fiscal electrónica) y documentos fiscales válidos para Brasil."},
            {"icon": "📱", "title": "Kiosko Automático", "body": "Registra la placa/modelo/costo y tu tienda online se crea sola con fotos, precio sugerido y ubicación Bodega/Estante."},
            {"icon": "💬", "title": "Venta por WhatsApp", "body": "Link personal para mandar por WhatsApp con stock real y ubicación Bodega/Estante."},
        ],
        "features_footer": "En Brasil: desmanche · oficina mecânica · loja de autopeças",
        "signup_url": "/br/signup/",
        "login_url": "/br/login/",
        "precios_url": "/br/precios/",
        "country_local": {
            "title": "Hecho para Brasil 🇧🇷",
            "subtitle": "Entendemos las necesidades específicas del sector automotriz brasileño",
            "items": [
                {"title": "✅ Conformidad Fiscal", "bullets": ["NF-e automático", "ICMS/IPI gestionados", "Control de impuestos", "CNPJ/CPF integrado"]},
                _MOBILE_LOCAL_ES,
                {"title": "💳 Pagos Locales", "bullets": ["PIX integrado", "Transferencias TED/DOC", "Tarjetas de crédito/débito", "Moneda local (BRL)"]},
            ],
        },
        "plans": [
            {"name": "Entry", "price": "R$ 100", "period": "por mes", "period_equiv": "≈ $20 USD / mes", "savings": None, "popular": False,
             "features": _LATAM_PLAN_FEATURES["entry"], "url": "/br/signup/?plan=entry"},
            {"name": "Growth", "price": "R$ 550", "period": "por 6 meses", "period_equiv": "≈ $110 USD / 6 meses", "savings": "Ahorra 17%", "popular": True,
             "features": _LATAM_PLAN_FEATURES["growth"], "url": "/br/signup/?plan=growth"},
            {"name": "Business", "price": "R$ 1.000", "period": "por año", "period_equiv": "≈ $200 USD / año", "savings": "Ahorra 33%", "popular": False,
             "features": _LATAM_PLAN_FEATURES["business"], "url": "/br/signup/?plan=business"},
        ],
        "meta_title": "eGarage Brasil — Software para Oficinas en São Paulo, Rio y Curitiba",
        "meta_description": "Software de gestão para oficinas mecânicas, desmanches e lojas de autopeças no Brasil. NF-e e PIX integrados. Teste grátis 30 dias.",
        "og_image": "img/welcome/br/og.png",
        "theme": {"primary": "#009C3B", "accent": "#FEDF00", "badge": _BADGE_SKY},
        "art_direction": _ART_BR,
        "cities": ["São Paulo", "Rio de Janeiro", "Belo Horizonte", "Curitiba", "Porto Alegre"],
        "vehicles": ["Onix", "Hilux", "Strada", "HB20", "Kwid"],
        "priority_rubro": "taller",
        "market_insight": {
            "headline": "Mais de 200,000 oficinas mecânicas operam no Brasil.",
            "tip": "A NF-e automática, o PIX e o controle de estoque são os pilares do setor automotivo.",
            "focus": "Com o eGarage você digitaliza sua oficina com NF-e automática e PIX integrado desde o primeiro dia.",
        },
        "social_proof": {"stats": [
            {"value": "200K+", "label": "oficinas no Brasil"},
            {"value": "NF-e", "label": "automática"},
            {"value": "30 dias", "label": "teste gratuito"},
        ]},
    },

    ("br", "pt"): {
        "html_lang": "pt-br",
        "country_name": "Brasil",
        "country_code": "br",
        "flag": "🇧🇷",
        "c1_rgb": "0, 156, 59",
        "c2_rgb": "254, 223, 0",
        "c1_hex": "#009C3B",
        "c2_hex": "#FEDF00",
        "btn_text_color": "#000000",
        "hero_subtitle": "Gestão digital para oficinas mecânicas, desmanches e lojas de autopeças em São Paulo, Rio de Janeiro e Curitiba",
        "hero_image": "img/welcome/br/hero.webp",
        "terminology": [
            {"label": "Veículo", "value": "Carro Usado"},
            {"label": "Documento", "value": "DUT / CRLV"},
            {"label": "Imposto", "value": "IPVA / ICMS"},
        ],
        "rubro_label": "Qual é o seu tipo de negócio?",
        "rubro_cards": [
            {"icon": "🔧", "title": "Oficina Mecânica", "subtitle": "Ordens de serviço, diagnósticos, clientes e veículos", "rubro": "taller"},
            {"icon": "🚗", "title": "Desmanche", "subtitle": "Inventário de peças, vendas por peça e rastreabilidade", "rubro": "desarmaduría"},
            {"icon": "📦", "title": "Loja de Autopeças", "subtitle": "Catálogo, estoque, orçamentos e controle de inventário", "rubro": "repuestos"},
        ],
        "rubro_extra": "Também: borracharia, car wash, lataria e pintura e mais...",
        "features_title": "Funcionalidades Poderosas",
        "features": [
            {"icon": "✅", "title": "Conformidade Fiscal Brasil", "body": "NF-e automática. ICMS/IPI/ISS gerenciados. Documentos fiscais válidos para o Brasil."},
            {"icon": "📱", "title": "Quiosque Automático", "body": "Cadastre a placa/modelo/custo e sua loja online é criada automaticamente com fotos, preço sugerido e localização Depósito/Prateleira."},
            {"icon": "💬", "title": "Venda pelo WhatsApp", "body": "Link pessoal para compartilhar pelo WhatsApp com estoque real e localização Depósito/Prateleira."},
        ],
        "features_footer": "No Brasil: desmanche · oficina mecânica · loja de autopeças",
        "business_types_title": "Feito para Todos os Negócios Automotivos",
        "business_types_subtitle": "Não importa o tipo de serviço automotivo, eGarage é perfeito para você",
        "business_types": [
            {"icon": "🔧", "title": "Oficinas Mecânicas", "body": "Gestão completa de ordens de serviço, diagnósticos, revisões e manutenções preventivas e corretivas."},
            {"icon": "🚗", "title": "Desmanches", "body": "Controle de veículos entrados, inventário de peças usadas, vendas por peça e rastreabilidade completa."},
            {"icon": "🛞", "title": "Borracharia e Vulcanização", "body": "Controle de pneus, rodízio, balanceamento, alinhamento e estoque."},
            {"icon": "⚙️", "title": "Lojas de Autopeças", "body": "Gestão de inventário, vendas, catálogo de peças, fornecedores e controle de entradas e saídas."},
            {"icon": "🔨", "title": "Lataria e Funilaria", "body": "Controle de reparações, amassados, soldas e restauração de carrocerias."},
            {"icon": "🎨", "title": "Pintura e Detalhamento", "body": "Gestão de serviços de pintura, polimento, vitrificação e acabamentos especiais."},
            {"icon": "🚗", "title": "Centro Automotivo", "body": "Solução completa para centros que oferecem múltiplos serviços."},
            {"icon": "⚡", "title": "Suspensão e Amortecedor", "body": "Especializado em sistemas de suspensão, amortecedores, molas e kits."},
            {"icon": "🔌", "title": "Elétrica Automotiva", "body": "Controle de serviços elétricos, injeção eletrônica, bateria, alternador e sistemas eletrônicos."},
        ],
        "more_title": "E muito mais!",
        "more_body": "Seja qual for o seu negócio no setor automotivo, o eGarage se adapta às suas necessidades específicas.",
        "cta_login": "🔐 Já tenho conta",
        "cta_precios": "💰 Ver Planos",
        "cta_start": "🚀 Teste Grátis",
        "popular_badge": "🏆 MAIS POPULAR",
        "plan_select": "Selecionar",
        "trial_title": "🎁 Teste Grátis por 30 Dias",
        "trial_text": "Sem cartão. Sem compromisso. Cancele quando quiser.",
        "pricing_title": "Planos Acessíveis",
        "pricing_subtitle": "Escolha o plano que melhor se adapta ao seu negócio",
        "signup_url": "/br/signup/",
        "login_url": "/br/login/",
        "precios_url": "/br/precos/",
        "lang_switcher": None,
        "country_local": {
            "title": "Feito para o Brasil 🇧🇷",
            "subtitle": "Entendemos as necessidades específicas das oficinas brasileiras",
            "items": [
                {"title": "✅ Conformidade Fiscal", "bullets": ["NF-e automática", "ICMS/IPI gerenciados", "Controle de impostos", "CNPJ/CPF integrado"]},
                {"title": "📱 Mobile First", "bullets": ["Interface otimizada para celular", "Funciona sem internet", "App nativo (em breve)", "Sincronização automática"]},
                {"title": "💳 Pagamentos Locais", "bullets": ["PIX integrado", "Transferências TED/DOC", "Cartões de crédito/débito", "Moeda local (BRL)"]},
            ],
        },
        "plans": [
            {"name": "Entry", "price": "R$ 100", "period": "por mês", "period_equiv": "≈ $20 USD / mês", "savings": None, "popular": False,
             "features": ["Veículos ilimitados", "Quiosque automático", "Localização Depósito-Prateleira", "Preço inteligente", "Suporte via WhatsApp"], "url": "/br/signup/?plan=entry"},
            {"name": "Growth", "price": "R$ 550", "period": "por 6 meses", "period_equiv": "≈ $110 USD / 6 meses", "savings": "Economize 17%", "popular": True,
             "features": ["Tudo do Entry", "Análises avançadas", "Multi-filiais", "Suporte prioritário"], "url": "/br/signup/?plan=growth"},
            {"name": "Business", "price": "R$ 1.000", "period": "por ano", "period_equiv": "≈ $200 USD / ano", "savings": "Economize 33%", "popular": False,
             "features": ["Tudo do Growth", "Treinamento incluído", "API personalizada", "Suporte dedicado"], "url": "/br/signup/?plan=business"},
        ],
        "meta_title": "eGarage Brasil — Software para Oficinas em São Paulo, Rio e Curitiba",
        "meta_description": "Software de gestão para oficinas mecânicas, desmanches e lojas de autopeças em todo o Brasil. NF-e automática, PIX integrado. Teste grátis 30 dias.",
        "og_image": "img/welcome/br/og.png",
        "theme": {"primary": "#009C3B", "accent": "#FEDF00", "badge": _BADGE_SKY},
        "art_direction": _ART_BR,
        "cities": ["São Paulo", "Rio de Janeiro", "Belo Horizonte", "Curitiba", "Porto Alegre"],
        "vehicles": ["Onix", "Hilux", "Strada", "HB20", "Kwid"],
        "priority_rubro": "taller",
        "market_insight": {
            "headline": "Mais de 200,000 oficinas mecânicas operam no Brasil.",
            "tip": "A NF-e automática, o PIX e o controle de estoque são os pilares do setor automotivo.",
            "focus": "Com o eGarage você digitaliza sua oficina com NF-e automática e PIX integrado desde o primeiro dia.",
        },
        "social_proof": {"stats": [
            {"value": "200K+", "label": "oficinas no Brasil"},
            {"value": "NF-e", "label": "automática"},
            {"value": "30 dias", "label": "teste gratuito"},
        ]},
    },

    ("us", "en"): {
        "html_lang": "en-us",
        "country_name": "USA",
        "country_code": "us",
        "flag": "🇺🇸",
        "c1_rgb": "0, 40, 104",
        "c2_rgb": "191, 10, 48",
        "c1_hex": "#002868",
        "c2_hex": "#BF0A30",
        "btn_text_color": "#ffffff",
        "hero_subtitle": "Shop management software for auto repair shops, salvage yards and parts stores in Miami, Houston and Texas",
        "hero_image": "img/welcome/us/hero.webp",
        "terminology": [
            {"label": "Vehicle", "value": "Used Car / Pre-owned"},
            {"label": "Title", "value": "Clean Title"},
            {"label": "Report", "value": "Carfax / Autocheck"},
        ],
        "rubro_label": "What type of business do you have?",
        "rubro_cards": [
            {"icon": "🔧", "title": "Auto Repair Shop", "subtitle": "Work orders, diagnostics, clients and vehicles", "rubro": "taller"},
            {"icon": "🚗", "title": "Salvage Yard", "subtitle": "Parts inventory, part-by-part sales and full traceability", "rubro": "desarmaduría"},
            {"icon": "📦", "title": "Parts Store", "subtitle": "Catalog, stock, quotes and inventory control", "rubro": "repuestos"},
        ],
        "rubro_extra": "Also: tire shops, body shops, paint shops and more...",
        "features_title": "Powerful Features",
        "features": [
            {"icon": "✅", "title": "US Tax Compliance", "body": "Automatic sales tax calculation by state. Valid fiscal documents: invoices, receipts, and work orders."},
            {"icon": "📱", "title": "Automatic Kiosk", "body": "Save VIN/make/model/cost and your online kiosk is created automatically with photos, suggested price, and Warehouse/Shelf location."},
            {"icon": "💬", "title": "WhatsApp / SMS Sales", "body": "Personal link to share via WhatsApp or SMS with real stock and Warehouse/Shelf location."},
        ],
        "features_footer": "In USA: salvage yard · auto repair shop · parts store",
        "business_types_title": "Made for All Automotive Businesses",
        "business_types_subtitle": "No matter what type of automotive service, eGarage is perfect for you",
        "business_types": _US_BUSINESS_TYPES,
        "more_title": "And much more!",
        "more_body": "Whatever your business in the automotive sector, eGarage adapts to your specific needs.",
        "cta_login": "🔐 Login",
        "cta_precios": "💰 View Plans",
        "cta_start": "🚀 Start Free",
        "popular_badge": "🏆 MOST POPULAR",
        "plan_select": "Select",
        "trial_title": "🎁 Try Free for 30 Days",
        "trial_text": "No credit card. No commitment. Cancel anytime.",
        "pricing_title": "Affordable Plans",
        "pricing_subtitle": "Choose the plan that best fits your business",
        "signup_url": "/us/signup/",
        "login_url": "/us/login/",
        "precios_url": "/us/pricing/",
        "lang_switcher": {"es_url": "/us/es/bienvenida/", "en_url": "/us/en/bienvenida/"},
        "country_local": {
            "title": "Made for the USA 🇺🇸",
            "subtitle": "We understand the specific needs of American auto shops",
            "items": [
                {"title": "✅ Tax Compliance", "bullets": ["Automatic sales tax by state", "Digital invoices", "Tax control", "Accounting integration"]},
                _MOBILE_LOCAL_EN,
                {"title": "💳 Local Payments", "bullets": ["Bank transfers", "Credit/debit cards", "Stripe integrated", "Local currency (USD)"]},
            ],
        },
        "plans": [
            {"name": "Entry", "price": "$20", "period": "USD per month", "period_equiv": None, "savings": None, "popular": False,
             "features": _US_PLAN_FEATURES["entry"], "url": "/us/signup/?plan=monthly"},
            {"name": "Growth", "price": "$110", "period": "USD every 6 months", "period_equiv": None, "savings": "Save 17%", "popular": True,
             "features": _US_PLAN_FEATURES["growth"], "url": "/us/signup/?plan=semi-annual"},
            {"name": "Business", "price": "$200", "period": "USD per year", "period_equiv": None, "savings": "Save 33%", "popular": False,
             "features": _US_PLAN_FEATURES["business"], "url": "/us/signup/?plan=annual"},
        ],
        "meta_title": "eGarage USA — Auto Shop Software | Miami, Houston, Texas",
        "meta_description": "Shop management software for auto repair shops, salvage yards and parts stores in the USA. Bilingual support, Carfax integration. Free trial 30 days.",
        "og_image": "img/welcome/us/og.png",
        "hero_headline": "The shop management software for auto businesses that want to grow.",
        "hero_subline": "Control your repair shop, parts store, salvage yard or car wash from anywhere.",
        "theme": {"primary": "#002868", "accent": "#BF0A30", "badge": _BADGE_SKY},
        "art_direction": _ART_US,
        "cities": ["Miami", "Houston", "Dallas", "Los Angeles", "Chicago"],
        "vehicles": ["F-150", "Silverado", "Ram 1500", "Camry", "Corolla"],
        "priority_rubro": "taller",
        "market_insight": {
            "headline": "Over 160,000 auto repair shops and salvage yards operate across the USA.",
            "tip": "Work order digitization, parts inventory control, and bilingual service are the main challenges.",
            "focus": "With eGarage you manage your shop with bilingual support and US tax compliance from day one.",
        },
        "social_proof": {"stats": [
            {"value": "160K+", "label": "shops in USA"},
            {"value": "Bilingual", "label": "EN / ES support"},
            {"value": "30 days", "label": "free trial"},
        ]},
    },

    ("us", "es"): {
        **_LATAM_COMMON_ES,
        "html_lang": "es-us",
        "country_name": "USA",
        "country_code": "us",
        "flag": "🇺🇸",
        "c1_rgb": "0, 40, 104",
        "c2_rgb": "191, 10, 48",
        "c1_hex": "#002868",
        "c2_hex": "#BF0A30",
        "btn_text_color": "#ffffff",
        "hero_subtitle": "Software de gestión para talleres, salvage yards y tiendas de repuestos en Miami, Houston y Texas",
        "hero_image": "img/welcome/us/hero.webp",
        "terminology": [
            {"label": "Vehículo", "value": "Used Car / Pre-owned"},
            {"label": "Título", "value": "Clean Title"},
            {"label": "Reporte", "value": "Carfax / Autocheck"},
        ],
        "rubro_cards": [
            {"icon": "🔧", "title": "Auto Repair Shop", "subtitle": "Órdenes de trabajo, diagnósticos, clientes y vehículos", "rubro": "taller"},
            {"icon": "🚗", "title": "Salvage Yard / Yarda", "subtitle": "Inventario de piezas, ventas por pieza y trazabilidad", "rubro": "desarmaduría"},
            {"icon": "📦", "title": "Tienda de Repuestos", "subtitle": "Catálogo, stock, cotizaciones y control de inventario", "rubro": "repuestos"},
        ],
        "rubro_extra": "También: tire shops, car wash, body shops y más...",
        "features": [
            {"icon": "✅", "title": "Cumplimiento Fiscal USA", "body": "Sales tax calculado automáticamente por estado. Documentos fiscales: facturas, recibos y órdenes de trabajo."},
            {"icon": "📱", "title": "Kiosko Automático", "body": "Guarda VIN/marca/modelo/costo y tu tienda online se crea sola con fotos, precio sugerido y ubicación Warehouse/Shelf."},
            {"icon": "💬", "title": "Ventas por WhatsApp / SMS", "body": "Link personal para compartir por WhatsApp con stock real y ubicación Warehouse/Shelf."},
        ],
        "features_footer": "En USA: salvage yard · auto repair shop · parts store",
        "business_types": _US_BUSINESS_TYPES,
        "signup_url": "/us/signup/",
        "login_url": "/us/login/",
        "precios_url": "/us/pricing/",
        "lang_switcher": {"es_url": "/us/es/bienvenida/", "en_url": "/us/en/bienvenida/"},
        "country_local": {
            "title": "Hecho para USA 🇺🇸",
            "subtitle": "Entendemos las necesidades específicas de los negocios automotrices en USA",
            "items": [
                {"title": "✅ Cumplimiento Fiscal", "bullets": ["Sales tax automático por estado", "Facturas digitales", "Control de impuestos", "Integración contable"]},
                _MOBILE_LOCAL_ES,
                {"title": "💳 Pagos Locales", "bullets": ["Transferencias bancarias", "Tarjetas de crédito/débito", "Stripe integrado", "Moneda local (USD)"]},
            ],
        },
        "plans": [
            {"name": "Entry", "price": "$20", "period": "USD por mes", "period_equiv": None, "savings": None, "popular": False,
             "features": _LATAM_PLAN_FEATURES["entry"], "url": "/us/signup/?plan=monthly"},
            {"name": "Growth", "price": "$110", "period": "USD por 6 meses", "period_equiv": None, "savings": "Ahorra 17%", "popular": True,
             "features": _LATAM_PLAN_FEATURES["growth"], "url": "/us/signup/?plan=semi-annual"},
            {"name": "Business", "price": "$200", "period": "USD por año", "period_equiv": None, "savings": "Ahorra 33%", "popular": False,
             "features": _LATAM_PLAN_FEATURES["business"], "url": "/us/signup/?plan=annual"},
        ],
        "meta_title": "eGarage USA — Software para Talleres en Miami, Houston y Texas",
        "meta_description": "Software de gestión para talleres mecánicos, salvage yards y tiendas de repuestos en USA. Soporte bilingüe y Carfax. Prueba gratis 30 días.",
        "og_image": "img/welcome/us/og.png",
        "theme": {"primary": "#002868", "accent": "#BF0A30", "badge": _BADGE_SKY},
        "art_direction": _ART_US,
        "cities": ["Miami", "Houston", "Dallas", "Los Angeles", "Chicago"],
        "vehicles": ["F-150", "Silverado", "Ram 1500", "Camry", "Corolla"],
        "priority_rubro": "taller",
        "market_insight": {
            "headline": "Más de 160,000 talleres mecánicos y salvage yards operan en USA.",
            "tip": "La digitalización de OTs, el control de inventario y el servicio bilingüe son los desafíos del rubro.",
            "focus": "Con eGarage gestionas tu taller con soporte bilingüe y cumplimiento fiscal USA desde el primer día.",
        },
        "social_proof": {"stats": [
            {"value": "160K+", "label": "talleres en USA"},
            {"value": "Bilingüe", "label": "soporte EN / ES"},
            {"value": "30 días", "label": "prueba gratuita"},
        ]},
    },
}


def get_config(country: str, lang: str) -> dict:
    """Return welcome config for a country+lang pair, falling back to (country, 'es').

    Injects global constants (PLATFORM_STATS, HERO_HEADLINE, HERO_SUBLINE,
    HERO_RUBRO_SCENES, DASHBOARD_SCENE) so templates receive them without extra imports.
    Per-country keys take precedence over globals.
    """
    config = WELCOME_CONFIG.get((country, lang))
    if config is None:
        config = WELCOME_CONFIG.get((country, "es"), {})
    if not config:
        return config
    return {
        "platform_stats": PLATFORM_STATS,
        "hero_headline": HERO_HEADLINE,
        "hero_subline": HERO_SUBLINE,
        "hero_rubro_scenes": HERO_RUBRO_SCENES,
        "dashboard_scene": DASHBOARD_SCENE,
        **config,
    }
