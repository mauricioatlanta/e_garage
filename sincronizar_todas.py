import os, re, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings_prod")
django.setup()

from taller.models.vehiculo_desarme import VehiculoDesarme
from taller.models.pieza_desarme import PiezaDesarme

# 1. Leer los slots exactos del SVG del Sedán
path_svg = "templates/taller/desarme/partials/vehicles/sedan_wireframe.html"
with open(path_svg, "r", encoding="utf-8") as f:
    slots_sedan = re.findall(r'data-slot=["\']([^"\']+)["\']', f.read())

print("Slots reales que existen en el auto:")
for s in slots_sedan:
    print(f"  • {s}")

v = VehiculoDesarme.objects.get(pk=162)

# Nombres amigables para cada slot encontrado
nombres_slots = {
    "door.front.left": ("Puerta Delantera Izquierda", 120000, "BODEGA"),
    "door.front.right": ("Puerta Delantera Derecha", 110000, "VEHICULO"),
    "door.rear.left": ("Puerta Trasera Izquierda", 95000, "VEHICULO"),
    "door.rear.right": ("Puerta Trasera Derecha", 95000, "BODEGA"),
    "hood": ("Capó Delantero", 85000, "VEHICULO"),
    "trunk": ("Maleta / Portón Trasero", 70000, "BODEGA"),
    "roof": ("Techo", 60000, "VEHICULO"),
    "bumper.front": ("Parachoques Delantero", 75000, "VEHICULO"),
    "bumper.rear": ("Parachoques Trasero", 65000, "VEHICULO"),
    "engine": ("Motor Completo", 450000, "VEHICULO"),
    "wheel.front.left": ("Rueda / Llanta Delantera Izquierda", 40000, "BODEGA"),
    "wheel.front.right": ("Rueda / Llanta Delantera Derecha", 40000, "VEHICULO"),
}

# Crear o actualizar piezas para los slots disponibles
for idx, slot in enumerate(slots_sedan, start=1):
    info = nombres_slots.get(slot, (f"Componente {slot}", 50000, "VEHICULO"))
    codigo = f"HYU-ACC-{v.id}-{slot.replace('.', '-')}"
    
    p = PiezaDesarme.objects.filter(vehiculo_desarme=v, visual_slot=slot).first() or \
        PiezaDesarme.objects.filter(vehiculo_desarme=v, codigo=codigo).first() or \
        PiezaDesarme(vehiculo_desarme=v, codigo=codigo)
    
    p.empresa = v.empresa
    p.visual_slot = slot
    p.ubicacion_tipo = info[2]
    p.origen = "DESARME_PROPIO"
    p.activo = True
    if hasattr(p, "nombre"):
        p.nombre = info[0]
    if hasattr(p, "precio_sugerido"):
        p.precio_sugerido = info[1]
    if hasattr(p, "precio"):
        p.precio = info[1]
    p.save()
    print(f"✅ Slot '{slot}' asignado a '{info[0]}' (${info[1]:,} CLP - {info[2]})")

print("\n🎯 Todas las zonas sincronizadas con éxito.")
