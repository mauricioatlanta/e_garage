import os, re, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings_prod")
django.setup()

from taller.models.vehiculo_desarme import VehiculoDesarme
from taller.models.pieza_desarme import PiezaDesarme

v = VehiculoDesarme.objects.get(pk=162)
empresa = v.empresa

# Buscar los slots definidos en los templates SVG del wireframe
slots_encontrados = set()
for path in [
    "templates/taller/desarme/partials/vehicles/sedan_wireframe.html",
    "templates/taller/desarme/partials/_vehiculo_mapa_visual.html"
]:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            slots_encontrados.update(re.findall(r'data-slot=["\']([^"\']+)["\']', f.read()))

print("Slots anatómicos encontrados en el SVG:", list(slots_encontrados)[:8])

# Definir 4 piezas de muestra para el Hyundai Accent
repuestos = [
    {
        "nombre": "Capó Original Delantero",
        "slot": next((s for s in slots_encontrados if "hood" in s or "capo" in s), "hood"),
        "precio": 85000,
        "ubicacion": "VEHICULO"
    },
    {
        "nombre": "Puerta Delantera Izquierda (Piloto)",
        "slot": next((s for s in slots_encontrados if "door.front.left" in s or ("door" in s and "left" in s)), "door.front.left"),
        "precio": 120000,
        "ubicacion": "BODEGA"
    },
    {
        "nombre": "Alternador 12V Original",
        "slot": next((s for s in slots_encontrados if "alternator" in s or "engine" in s), "engine.alternator"),
        "precio": 65000,
        "ubicacion": "BODEGA"
    },
    {
        "nombre": "Parachoques Delantero",
        "slot": next((s for s in slots_encontrados if "front.bumper" in s or "bumper" in s), "front.bumper"),
        "precio": 75000,
        "ubicacion": "VEHICULO"
    },
]

for idx, item in enumerate(repuestos, start=1):
    codigo = f"HYU-ACC-{v.id}-{idx:03d}"
    p = PiezaDesarme.objects.filter(vehiculo_desarme=v, codigo=codigo).first() or PiezaDesarme(vehiculo_desarme=v, codigo=codigo)
    p.empresa = empresa
    if hasattr(p, "nombre"):
        p.nombre = item["nombre"]
    if hasattr(p, "precio_sugerido"):
        p.precio_sugerido = item["precio"]
    if hasattr(p, "precio"):
        p.precio = item["precio"]
    if hasattr(p, "ubicacion_tipo"):
        p.ubicacion_tipo = item["ubicacion"]
    if hasattr(p, "visual_slot"):
        p.visual_slot = item["slot"]
    if hasattr(p, "origen"):
        p.origen = "DESARME_PROPIO"
    if hasattr(p, "activo"):
        p.activo = True
    p.save()
    print(f"✅ Repuesto sincronizado: {item['nombre']} -> Slot '{item['slot']}' (${item['precio']:,} CLP)")

print("\n🎯 ¡Listo! 4 piezas vinculadas al Gemelo Digital.")
