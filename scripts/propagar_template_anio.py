#!/usr/bin/env python3
import shutil

# Template fuente
template_source = "templates_canonical/taller/vehiculos/crear_vehiculo.html"

# Templates destino (multiples idiomas)
templates_destino = [
    "templates/CL/ES/taller/vehiculos/crear_vehiculo.html",
    "templates/CL/EN/taller/vehiculos/crear_vehiculo.html",
    "templates/US/ES/taller/vehiculos/crear_vehiculo.html",
    "templates/US/EN/taller/vehiculos/crear_vehiculo.html",
]

print("🔄 Propagando template con atributo required en campo año...")

# Copiar archivo a todos los idiomas
for destino in templates_destino:
    try:
        shutil.copy2(template_source, destino)
        print(f"✅ Copiado a {destino}")
    except Exception as e:
        print(f"❌ Error copiando a {destino}: {e}")

print("\n✅ Template con required en año propagado a todas las variantes")
print("✨ Listo para probar creación de vehículos!")
