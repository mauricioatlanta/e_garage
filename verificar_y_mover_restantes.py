"""Verificar y mover archivos restantes de taller/cl/es y taller/us."""

from pathlib import Path
import shutil

BASE_DIR = Path(r"E:\projecto\e_garage")

# Archivos que deben moverse
archivos_a_mover = [
    # CL/ES
    ("templates/taller/cl/es/vehiculos/crear.html", "templates/cl/es/vehiculos/crear.html"),
    (
        "templates/taller/cl/es/repuestos/repuesto_list.html",
        "templates/cl/es/repuestos/repuesto_list.html",
    ),
    (
        "templates/taller/cl/es/servicios/servicios_menu.html",
        "templates/cl/es/servicios/servicios_menu.html",
    ),
    (
        "templates/taller/cl/es/documentos/base_documento.html",
        "templates/cl/es/documentos/base_documento.html",
    ),
    (
        "templates/taller/cl/es/documentos/crear_documento.html",
        "templates/cl/es/documentos/crear_documento.html",
    ),
    # US/EN
    ("templates/taller/us/en/vehiculos/crear.html", "templates/us/en/vehiculos/crear.html"),
    (
        "templates/taller/us/en/vehiculos/crear_vehiculo.html",
        "templates/us/en/vehiculos/crear_vehiculo.html",
    ),
    ("templates/taller/us/en/vehiculos/detalle.html", "templates/us/en/vehiculos/detalle.html"),
    ("templates/taller/us/en/vehiculos/editar.html", "templates/us/en/vehiculos/editar.html"),
    (
        "templates/taller/us/en/vehiculos/editar_vehiculo.html",
        "templates/us/en/vehiculos/editar_vehiculo.html",
    ),
    (
        "templates/taller/us/en/vehiculos/lista_vehiculos.html",
        "templates/us/en/vehiculos/lista_vehiculos.html",
    ),
    (
        "templates/taller/us/en/vehiculos/vehiculo_list.html",
        "templates/us/en/vehiculos/vehiculo_list.html",
    ),
    (
        "templates/taller/us/en/vehiculos/vehiculo_list_simple.html",
        "templates/us/en/vehiculos/vehiculo_list_simple.html",
    ),
    (
        "templates/taller/us/en/servicios/crear_otro_servicio.html",
        "templates/us/en/servicios/crear_otro_servicio.html",
    ),
    (
        "templates/taller/us/en/servicios/otros_servicios_menu.html",
        "templates/us/en/servicios/otros_servicios_menu.html",
    ),
    (
        "templates/taller/us/en/servicios/servicios_menu.html",
        "templates/us/en/servicios/servicios_menu.html",
    ),
    (
        "templates/taller/us/en/documentos/base_documento.html",
        "templates/us/en/documentos/base_documento.html",
    ),
    (
        "templates/taller/us/en/documentos/crear_documento.html",
        "templates/us/en/documentos/crear_documento.html",
    ),
    (
        "templates/taller/us/en/documentos/crear_documento_moderno.html",
        "templates/us/en/documentos/crear_documento_moderno.html",
    ),
    (
        "templates/taller/us/en/documentos/crear_repuesto.html",
        "templates/us/en/documentos/crear_repuesto.html",
    ),
    (
        "templates/taller/us/en/documentos/crear_tienda.html",
        "templates/us/en/documentos/crear_tienda.html",
    ),
    (
        "templates/taller/us/en/documentos/editar_documento_nuevo.html",
        "templates/us/en/documentos/editar_documento_nuevo.html",
    ),
    (
        "templates/taller/us/en/documentos/lista_documentos.html",
        "templates/us/en/documentos/lista_documentos.html",
    ),
    (
        "templates/taller/us/en/settings/futuristic_company_settings.html",
        "templates/us/en/settings/futuristic_company_settings.html",
    ),
    # US/ES
    (
        "templates/taller/us/es/vehiculos/crear_vehiculo.html",
        "templates/us/es/vehiculos/crear_vehiculo.html",
    ),
    (
        "templates/taller/us/es/servicios/crear_otro_servicio.html",
        "templates/us/es/servicios/crear_otro_servicio.html",
    ),
    (
        "templates/taller/us/es/documentos/crear_documento_moderno.html",
        "templates/us/es/documentos/crear_documento_moderno.html",
    ),
    (
        "templates/taller/us/es/documentos/crear_repuesto.html",
        "templates/us/es/documentos/crear_repuesto.html",
    ),
    (
        "templates/taller/us/es/documentos/crear_tienda.html",
        "templates/us/es/documentos/crear_tienda.html",
    ),
]

print("=" * 80)
print("MOVIENDO ARCHIVOS RESTANTES POR PAÍS")
print("=" * 80)

moved = 0
skipped = 0

for src_path, dst_path in archivos_a_mover:
    src = BASE_DIR / src_path
    dst = BASE_DIR / dst_path

    if not src.exists():
        print(f"[SKIP] No existe: {src_path}")
        skipped += 1
        continue

    if dst.exists():
        print(f"[SKIP] Ya existe: {dst_path}")
        skipped += 1
        continue

    print(f"[MOVE] {src_path} -> {dst_path}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))
    moved += 1

print("\n" + "=" * 80)
print(f"Movidos: {moved}, Omitidos: {skipped}")
print("=" * 80)
