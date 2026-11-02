from django.shortcuts import render
from django.contrib.auth.decorators import login_required

_RUBRO_CONFIG = {
    # Foundation: Taller
    "WORKSHOP": {
        "emoji": "🔧",
        "titulo": "Tu taller ya está listo.",
        "frase": "Registremos el primer vehículo.",
        "cta_texto": "Crear vehículo →",
        "color": "cyan",
        "glow": "cyan",
        "pasos": [
            "Crea tu primer vehículo",
            "Registra la primera orden de trabajo",
            "Revisa el historial desde el Dashboard",
        ],
    },
    "WORKSHOP_MOTO": {
        "emoji": "🔧",
        "titulo": "Tu taller ya está listo.",
        "frase": "Registremos la primera moto.",
        "cta_texto": "Crear vehículo →",
        "color": "cyan",
        "glow": "cyan",
        "pasos": [
            "Crea tu primera moto",
            "Registra la primera orden de trabajo",
            "Revisa el historial desde el Dashboard",
        ],
    },
    "WORKSHOP_HEAVY": {
        "emoji": "🔧",
        "titulo": "Tu taller ya está listo.",
        "frase": "Registremos el primer vehículo.",
        "cta_texto": "Crear vehículo →",
        "color": "cyan",
        "glow": "cyan",
        "pasos": [
            "Crea tu primer vehículo",
            "Registra la primera orden de trabajo",
            "Revisa el historial desde el Dashboard",
        ],
    },
    # Foundation: Casa de Repuestos
    "PARTS": {
        "emoji": "🏪",
        "titulo": "Tu catálogo está listo para cargar.",
        "frase": "Empieza con los repuestos que más vendes.",
        "cta_texto": "Crear primer repuesto →",
        "color": "lime",
        "glow": "lime",
        "pasos": [
            "Carga tus primeras referencias",
            "Tu catálogo queda publicado automáticamente",
            "El primer pedido llega solo",
        ],
    },
    # Foundation: Desarmaduría
    "DESARMADURIA": {
        "emoji": "🔩",
        "titulo": "Tu desarmaduría ya está lista.",
        "frase": "Ingresa el primer vehículo para desarmarlo.",
        "cta_texto": "Ingresar vehículo →",
        "color": "fuchsia",
        "glow": "fuchsia",
        "pasos": [
            "Ingresa el vehículo",
            "Marca las piezas disponibles",
            "Las piezas quedan publicadas automáticamente",
        ],
    },
}

_DEFAULT_CONFIG = {
    "emoji": "⚙️",
    "titulo": "Tu cuenta está lista.",
    "frase": "Empieza a explorar el sistema.",
    "cta_texto": "Ir al Dashboard →",
    "color": "cyan",
    "glow": "cyan",
    "pasos": [
        "Explora el sistema",
        "Crea tu primer registro",
        "Revisa los reportes desde el Dashboard",
    ],
}

_CTA_URLS = {
    "WORKSHOP":       "/cl/es/vehiculos/crear/",
    "WORKSHOP_MOTO":  "/cl/es/vehiculos/crear/",
    "WORKSHOP_HEAVY": "/cl/es/vehiculos/crear/",
    "PARTS":          "/cl/es/repuestos/crear/",
    "DESARMADURIA":   "/cl/es/desarme/vehiculos/crear/",
}

_DASHBOARD_URL = "/cl/es/centro-operaciones/"


@login_required
def primer_paso_chile(request):
    rubro = None
    try:
        config_obj = request.user.empresa.configuracionempresa
        rubro = config_obj.rubro_principal
    except Exception:
        pass

    cfg = _RUBRO_CONFIG.get(rubro, _DEFAULT_CONFIG)
    cta_url = _CTA_URLS.get(rubro, _DASHBOARD_URL)

    context = {
        **cfg,
        "cta_url": cta_url,
        "dashboard_url": _DASHBOARD_URL,
        "empresa_nombre": getattr(getattr(request.user, "empresa", None), "nombre_taller", ""),
    }
    return render(request, "onboarding/primer_paso.html", context)
