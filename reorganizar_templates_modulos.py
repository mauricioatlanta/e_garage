"""
Script para reorganizar templates por módulos según análisis detallado.

Estructura objetivo:
- COMMON: templates/taller/common/{modulo}/
- POR PAÍS: templates/{pais}/{idioma}/{modulo}/
- ARCHIVE: templates/_archive/{fecha}/{modulo}/
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
from collections import defaultdict

BASE_DIR = Path(r"E:\projecto\e_garage")
TEMPLATES_DIR = BASE_DIR / "templates"
ARCHIVE_DIR = TEMPLATES_DIR / "_archive"
ARCHIVE_DATE = datetime.now().strftime("%Y%m%d_%H%M%S")

# Mapeo de archivos COMMON a consolidar
COMMON_MAPPINGS = {
    "clientes": {
        "common": [
            "templates/taller/common/clientes/cliente_form.html",
            "templates/taller/common/clientes/cliente_list.html",
            "templates/taller/common/clientes/ver_cliente.html",
        ],
        "partials": [
            "templates/taller/clientes/_tabla_clientes.html",
        ],
        "candidates_to_common": [
            # El más moderno (con fondo espacial) debería ser el COMMON
            "templates/taller/clientes/cliente_form.html",  # Tiene fondo espacial futurista
            "templates/taller/clientes/cliente_list.html",
            "templates/taller/clientes/ver_cliente.html",
        ],
        "to_archive": [
            "templates/taller/clientes/cliente_detail.html",
            "templates/taller/clientes/confirmar_eliminacion.html",
            "templates/taller/clientes/editar_cliente.html",
            "templates/taller/clientes/eliminar_confirmar.html",
            "templates/taller/clientes/lista_clientes.html",
            "templates/taller/clientes/debug_cliente.html",
            "templates/clientes/cliente_list.html",  # Versiones antiguas
            "templates/clientes/crear_cliente.html",
            "templates/clientes/lista_clientes.html",
        ],
    },
    "vehiculos": {
        "common": [
            "templates/taller/common/vehiculos/vehiculo_list.html",
        ],
        "candidates_to_common": [
            "templates/taller/vehiculos/vehiculo_form.html",
            "templates/taller/vehiculos/vehiculo_detail.html",
            "templates/taller/vehiculos/_tabla_vehiculos.html",
            "templates/taller/vehiculos/form_marca_modal.html",
        ],
        "to_archive": [
            "templates/taller/vehiculos/crear_vehiculo.html",
            "templates/taller/vehiculos/editar_vehiculo.html",
            "templates/taller/vehiculos/detalle.html",
            "templates/taller/vehiculos/eliminar_confirmar.html",
            "templates/taller/vehiculos/vehiculos.html",
            "templates/taller/vehiculos/vehiculos_fixed.html",
            "templates/taller/vehiculos/editar.html",
            "templates/taller/vehiculos/debug_form.html",
            "templates/taller/vehiculos/crear_motor_simple.html",
            "templates/taller/vehiculos/crear_caja_simple.html",
            "templates/taller/vehiculos/close_and_notify.html",
        ],
    },
    "repuestos": {
        "common": [
            "templates/taller/common/repuestos/repuesto_list.html",
        ],
        "candidates_to_common": [
            # Elegir el más reciente/limpio
            "templates/taller/repuestos/repuesto_form_final.html",
            "templates/taller/repuestos/repuesto_form_new_clean.html",
            "templates/taller/repuestos/dashboard_repuestos.html",
            "templates/taller/repuestos/tabla_repuestos.html",
        ],
        "to_archive": [
            # Todos los formularios de prueba
            "templates/taller/repuestos/repuesto_form.html",
            "templates/taller/repuestos/repuesto_form_backup.html",
            "templates/taller/repuestos/repuesto_form_clean.html",
            "templates/taller/repuestos/repuesto_form_limpio.html",
            "templates/taller/repuestos/repuesto_form_new.html",
            "templates/taller/repuestos/repuesto_form_nuevo.html",
            "templates/taller/repuestos/agregar_repuesto.html",
            "templates/taller/repuestos/editar_repuesto.html",
            "templates/taller/repuestos/eliminar_repuesto.html",
            "templates/taller/repuestos/formulario_repuestos.html",
            "templates/taller/repuestos/lista_repuestos.html",
            "templates/taller/repuestos/listar_repuestos.html",
            "templates/taller/repuestos/repuesto_detail.html",
            "templates/taller/repuestos/tabla_repuestos_ajax.html",
            "templates/taller/repuestos/confirmar_eliminacion.html",
            "templates/taller/repuestos/eliminar_confirmar.html",
            "templates/taller/repuestos/reporte_repuestos.html",
        ],
    },
    "servicios": {
        "common": [
            "templates/taller/common/servicios/servicios_menu.html",
            "templates/taller/common/servicios/otros_servicios_menu.html",
        ],
        "candidates_to_common": [
            "templates/taller/servicios/crear_servicio.html",
            "templates/taller/servicios/servicio_list.html",
            "templates/taller/otros_servicios/otros_servicios_list.html",
        ],
        "to_archive": [
            "templates/taller/servicios/editar_servicio.html",
            "templates/taller/servicios/lista_servicios.html",
            "templates/taller/servicios/categorias_servicios.html",
            "templates/taller/servicios/lista_categorias.html",
            "templates/taller/servicios/tabla_servicios.html",
            "templates/taller/servicios/explorador_servicios.html",
            "templates/taller/servicios/servicios.html",
            "templates/taller/servicios/servicios_local.html",
            "templates/taller/servicios/lista.html",
            "templates/taller/servicios/formulario_servicio.html",
            "templates/taller/servicios/reporte_servicios.html",
            "templates/servicios/servicios_menu.html",  # Versiones antiguas
            "templates/servicios/otros_servicios_menu.html",
        ],
    },
    "documentos": {
        "common": [
            "templates/taller/common/documentos/base_documento.html",
            "templates/taller/common/documentos/document_form.html",
            "templates/taller/common/documentos/lista_documentos.html",
            "templates/taller/common/documentos/ver_documento_nuevo.html",
        ],
        "candidates_to_common": [
            # Base PDF
            "templates/taller/documentos/base/pdf_base.html",
            "templates/taller/documentos/base/includes/pdf_signatures.html",
            "templates/taller/documentos/base/includes/pdf_totals_payment.html",
            # Temas
            "templates/taller/documentos/_document_theme.html",
            "templates/taller/documentos/_document_theme_dark.html",
            "templates/taller/documentos/_document_theme_print.html",
        ],
        "to_archive": [
            "templates/taller/documentos/pdf_template.html",
            "templates/taller/documentos/pdf_base.html",  # Si hay duplicado
            "templates/taller/documentos/ver_documento.html",
            "templates/taller/documentos/opciones_entrega.html",
            "templates/taller/documentos/enviar_email_form.html",
            "templates/taller/documentos/ejemplo_totales_pdf.html",
            "templates/taller/documentos/ejemplo_modo_oscuro.html",
            "templates/taller/documentos/editar_ejemplo.html",
            "templates/taller/documentos/crear_ejemplo.html",
            "templates/taller/common/documentos/document_form_alpine_example.html",
            "templates/taller/common/documentos/document_edit.html",
            "templates/taller/common/documentos/editar_documento_nuevo.html",
            "templates/documentos/documento_form.html",  # Versión antigua
        ],
    },
    "reportes": {
        "common": [
            # Todo es COMMON, no hay por país
            "templates/taller/reportes/comparativo_precios.html",
            "templates/taller/reportes/dashboard.html",
            "templates/taller/reportes/dashboard_inteligencia.html",
            "templates/taller/reportes/dashboard_inteligencia_operativa.html",
            "templates/taller/reportes/dashboard_rentabilidad.html",
            "templates/taller/reportes/diagnostico_ia.html",
            "templates/taller/reportes/rentabilidad.html",
            "templates/taller/reportes/reportes.html",
            "templates/taller/reportes/reportes_mecanicos.html",
            "templates/taller/reportes/reportes_mecanicos_i18n.html",
            "templates/taller/reportes/reportes_por_fecha.html",
            "templates/taller/reportes/demo_reportes_por_fecha.html",
            "templates/taller/reportes/pdf_mecanico.html",
            "templates/taller/reportes/servicios_fecha.html",
            "templates/taller/reportes/servicios_subcontratados.html",
            "templates/taller/reportes/repuestos_fecha.html",
            "templates/taller/reportes/reporte_servicios.html",
            "templates/taller/reportes/reporte_repuestos.html",
            "templates/taller/reportes/otros_servicios_fecha.html",
            "templates/taller/dashboard/panel_reportes.html",
        ],
        "to_archive": [
            "templates/taller/reportes/servicios_subcontratados_backup.html",
        ],
    },
    "settings": {
        "candidates_to_common": [
            "templates/ejemplos/company_settings_form_unified.html",  # El más completo
        ],
        "to_archive": [
            "templates/settings/company_settings.html",
            "templates/settings/company_settings_es.html",
        ],
    },
}

# Archivos por país que DEBEN mantenerse en su ubicación actual
COUNTRY_SPECIFIC = {
    "cl/es/clientes": [
        "templates/cl/es/clientes/_tabla_clientes.html",
        "templates/cl/es/clientes/cliente_form.html",
        "templates/cl/es/clientes/cliente_list.html",
        "templates/cl/es/clientes/confirmar_eliminacion.html",
        "templates/cl/es/clientes/debug_cliente.html",
        "templates/cl/es/clientes/editar_cliente.html",
        "templates/cl/es/clientes/eliminar_confirmar.html",
        "templates/cl/es/clientes/ver_cliente.html",
    ],
    "us/en/clientes": [
        "templates/us/en/clientes/cliente_form.html",
        "templates/us/en/clientes/cliente_list.html",
        "templates/us/en/clientes/editar_cliente.html",
        "templates/us/en/clientes/lista_clientes.html",
        "templates/us/en/clientes/ver_cliente.html",
    ],
    "us/es/clientes": [
        "templates/us/es/clientes/cliente_form.html",
        "templates/us/es/clientes/cliente_list.html",
        "templates/us/es/clientes/editar_cliente.html",
        "templates/us/es/clientes/lista_clientes.html",
        "templates/us/es/clientes/ver_cliente.html",
    ],
    "cl/es/vehiculos": [
        "templates/cl/es/vehiculos/crear.html",  # Después de mover
        "templates/taller/cl/es/vehiculos/crear.html",  # Antes de mover
    ],
    "us/en/vehiculos": [
        "templates/us/en/vehiculos/crear.html",  # Después de mover
        "templates/us/en/vehiculos/crear_vehiculo.html",
        "templates/us/en/vehiculos/detalle.html",
        "templates/us/en/vehiculos/editar.html",
        "templates/us/en/vehiculos/editar_vehiculo.html",
        "templates/us/en/vehiculos/lista_vehiculos.html",
        "templates/us/en/vehiculos/vehiculo_list.html",
        "templates/us/en/vehiculos/vehiculo_list_simple.html",
        # También aceptar rutas antiguas antes de mover
        "templates/taller/us/en/vehiculos/crear.html",
        "templates/taller/us/en/vehiculos/crear_vehiculo.html",
        "templates/taller/us/en/vehiculos/detalle.html",
        "templates/taller/us/en/vehiculos/editar.html",
        "templates/taller/us/en/vehiculos/editar_vehiculo.html",
        "templates/taller/us/en/vehiculos/lista_vehiculos.html",
        "templates/taller/us/en/vehiculos/vehiculo_list.html",
        "templates/taller/us/en/vehiculos/vehiculo_list_simple.html",
    ],
    "us/es/vehiculos": [
        "templates/us/es/vehiculos/crear_vehiculo.html",  # Después de mover
        "templates/taller/us/es/vehiculos/crear_vehiculo.html",  # Antes de mover
    ],
    "cl/es/repuestos": [
        "templates/cl/es/repuestos/repuesto_list.html",  # Después de mover
        "templates/taller/cl/es/repuestos/repuesto_list.html",  # Antes de mover
    ],
    "cl/es/servicios": [
        "templates/cl/es/servicios/servicios_menu.html",  # Después de mover
        "templates/taller/cl/es/servicios/servicios_menu.html",  # Antes de mover
    ],
    "us/en/servicios": [
        "templates/us/en/servicios/crear_otro_servicio.html",  # Después de mover
        "templates/us/en/servicios/otros_servicios_menu.html",
        "templates/us/en/servicios/servicios_menu.html",
        # También aceptar rutas antiguas
        "templates/taller/us/en/servicios/crear_otro_servicio.html",
        "templates/taller/us/en/servicios/otros_servicios_menu.html",
        "templates/taller/us/en/servicios/servicios_menu.html",
    ],
    "us/es/servicios": [
        "templates/us/es/servicios/crear_otro_servicio.html",  # Después de mover
        "templates/taller/us/es/servicios/crear_otro_servicio.html",  # Antes de mover
    ],
    "cl/es/documentos": [
        "templates/cl/es/documentos/base_documento.html",  # Después de mover
        "templates/cl/es/documentos/crear_documento.html",
        # También aceptar rutas antiguas
        "templates/taller/cl/es/documentos/base_documento.html",
        "templates/taller/cl/es/documentos/crear_documento.html",
        "templates/taller/documentos/cl/es/documento_form.html",
        "templates/taller/documentos/cl/es/documento_editar.html",
    ],
    "us/en/documentos": [
        "templates/us/en/documentos/base_documento.html",  # Después de mover
        "templates/us/en/documentos/crear_documento.html",
        "templates/us/en/documentos/crear_documento_moderno.html",
        "templates/us/en/documentos/crear_repuesto.html",
        "templates/us/en/documentos/crear_tienda.html",
        "templates/us/en/documentos/editar_documento_nuevo.html",
        "templates/us/en/documentos/lista_documentos.html",
        # También aceptar rutas antiguas
        "templates/taller/us/en/documentos/base_documento.html",
        "templates/taller/us/en/documentos/crear_documento.html",
        "templates/taller/us/en/documentos/crear_documento_moderno.html",
        "templates/taller/us/en/documentos/crear_repuesto.html",
        "templates/taller/us/en/documentos/crear_tienda.html",
        "templates/taller/us/en/documentos/editar_documento_nuevo.html",
        "templates/taller/us/en/documentos/lista_documentos.html",
        "templates/taller/documentos/us/en/document_form.html",
        "templates/taller/documentos/us/en/document_form_select2.html",
        "templates/taller/documentos/us/en/document_list.html",
        "templates/taller/documentos/us/en/futurista/document_form_futuristic.html",
    ],
    "us/es/documentos": [
        "templates/us/es/documentos/crear_documento_moderno.html",  # Después de mover
        "templates/us/es/documentos/crear_repuesto.html",
        "templates/us/es/documentos/crear_tienda.html",
        # También aceptar rutas antiguas
        "templates/taller/us/es/documentos/crear_documento_moderno.html",
        "templates/taller/us/es/documentos/crear_repuesto.html",
        "templates/taller/us/es/documentos/crear_tienda.html",
        "templates/taller/documentos/us/es/futurista/documento_form_futurista.html",
    ],
    "us/en/settings": [
        "templates/us/en/settings/futuristic_company_settings.html",  # Después de mover
        "templates/taller/us/en/settings/futuristic_company_settings.html",  # Antes de mover
    ],
}


def ensure_dir(path: Path):
    """Asegura que el directorio existe."""
    path.mkdir(parents=True, exist_ok=True)


def move_file(src: Path, dst: Path, dry_run: bool = True):
    """Mueve un archivo, creando directorios si es necesario."""
    if not src.exists():
        print(f"[WARN] No existe: {src}")
        return False

    if dst.exists():
        print(f"[WARN] DESTINO YA EXISTE, no muevo: {src} -> {dst}")
        return False

    print(
        f"{'DRY-RUN ' if dry_run else 'MOVE    '} {src.relative_to(BASE_DIR)} -> {dst.relative_to(BASE_DIR)}"
    )
    if not dry_run:
        ensure_dir(dst.parent)
        shutil.move(str(src), str(dst))
    return True


def copy_file(src: Path, dst: Path, dry_run: bool = True):
    """Copia un archivo, creando directorios si es necesario."""
    if not src.exists():
        print(f"[WARN] No existe: {src}")
        return False

    print(
        f"{'DRY-RUN ' if dry_run else 'COPY    '} {src.relative_to(BASE_DIR)} -> {dst.relative_to(BASE_DIR)}"
    )
    if not dry_run:
        ensure_dir(dst.parent)
        shutil.copy2(str(src), str(dst))
    return True


def consolidate_common(dry_run: bool = True):
    """Consolida archivos COMMON según el mapeo."""
    print("\n" + "=" * 80)
    print("CONSOLIDACIÓN DE ARCHIVOS COMMON")
    print("=" * 80)

    for modulo, config in COMMON_MAPPINGS.items():
        print(f"\n--- MÓDULO: {modulo.upper()} ---")

        # 1. Mover candidatos a common (reemplazando si es necesario)
        if "candidates_to_common" in config:
            for candidate_path in config["candidates_to_common"]:
                src = BASE_DIR / candidate_path
                if not src.exists():
                    continue

                # Determinar nombre destino en common
                filename = src.name
                if modulo == "repuestos" and "repuesto_form" in filename:
                    # Para repuestos, elegir el más reciente y renombrarlo
                    if "final" in filename or "new_clean" in filename:
                        dst = BASE_DIR / f"templates/taller/common/{modulo}/repuesto_form.html"
                    else:
                        continue
                elif modulo == "settings" and "company_settings_form_unified" in filename:
                    dst = BASE_DIR / f"templates/settings/company_settings_common.html"
                else:
                    dst = BASE_DIR / f"templates/taller/common/{modulo}/{filename}"

                # Solo mover si el destino no existe o si el candidato es más reciente
                if not dst.exists() or src.stat().st_mtime > dst.stat().st_mtime:
                    move_file(src, dst, dry_run)
                else:
                    print(f"[SKIP] {src.name} - destino más reciente o igual")

        # 2. Mover partials a common
        if "partials" in config:
            for partial_path in config["partials"]:
                src = BASE_DIR / partial_path
                if not src.exists():
                    continue

                filename = src.name
                dst = BASE_DIR / f"templates/taller/common/{modulo}/{filename}"
                move_file(src, dst, dry_run)


def archive_duplicates(dry_run: bool = True):
    """Mueve archivos duplicados/antiguos a _archive."""
    print("\n" + "=" * 80)
    print("ARCHIVADO DE DUPLICADOS Y VERSIONES ANTIGUAS")
    print("=" * 80)

    archive_base = ARCHIVE_DIR / ARCHIVE_DATE

    for modulo, config in COMMON_MAPPINGS.items():
        if "to_archive" not in config:
            continue

        print(f"\n--- ARCHIVANDO {modulo.upper()} ---")
        for archive_path in config["to_archive"]:
            src = BASE_DIR / archive_path
            if not src.exists():
                continue

            # Mantener estructura relativa en archive
            rel_path = src.relative_to(TEMPLATES_DIR)
            dst = archive_base / rel_path

            move_file(src, dst, dry_run)


def move_country_files_to_correct_location(dry_run: bool = True):
    """Mueve archivos de taller/cl/es y taller/us a cl/es y us."""
    print("\n" + "=" * 80)
    print("REUBICACIÓN DE ARCHIVOS POR PAÍS")
    print("=" * 80)

    # Mover de taller/cl/es/* a cl/es/*
    for path in BASE_DIR.rglob("templates/taller/cl/es/*"):
        if path.is_dir():
            continue
        if "_archive" in str(path):
            continue

        rel = path.relative_to(BASE_DIR)
        new_rel = Path(str(rel).replace("templates/taller/cl/es/", "templates/cl/es/"))
        dst = BASE_DIR / new_rel

        # Evitar mover si el destino es el mismo que el origen
        if str(rel) == str(new_rel):
            continue

        # Verificar si debe mantenerse en taller/ (archivos específicos que no se mueven)
        # Por ahora, mover todos los de taller/cl/es a cl/es
        move_file(path, dst, dry_run)

    # Mover de taller/us/en/* a us/en/*
    for path in BASE_DIR.rglob("templates/taller/us/en/*"):
        if path.is_dir():
            continue
        if "_archive" in str(path):
            continue

        rel = path.relative_to(BASE_DIR)
        new_rel_str = str(rel).replace("templates/taller/us/en/", "templates/us/en/")
        new_rel = Path(new_rel_str)
        dst = BASE_DIR / new_rel

        # Evitar mover si el destino es el mismo que el origen
        if str(rel) == new_rel_str:
            continue

        move_file(path, dst, dry_run)

    # Mover de taller/us/es/* a us/es/*
    for path in BASE_DIR.rglob("templates/taller/us/es/*"):
        if path.is_dir():
            continue
        if "_archive" in str(path):
            continue

        rel = path.relative_to(BASE_DIR)
        new_rel_str = str(rel).replace("templates/taller/us/es/", "templates/us/es/")
        new_rel = Path(new_rel_str)
        dst = BASE_DIR / new_rel

        # Evitar mover si el destino es el mismo que el origen
        if str(rel) == new_rel_str:
            continue

        move_file(path, dst, dry_run)


def verify_country_specific(dry_run: bool = True):
    """Verifica que los archivos por país estén en su lugar correcto."""
    print("\n" + "=" * 80)
    print("VERIFICACIÓN DE ARCHIVOS POR PAÍS")
    print("=" * 80)

    for country_path, files in COUNTRY_SPECIFIC.items():
        print(f"\n--- {country_path.upper()} ---")
        for file_path in files:
            src = BASE_DIR / file_path
            if src.exists():
                print(f"[OK] {file_path}")
            else:
                print(f"[MISSING] {file_path}")


def reorganize_repuestos_form(dry_run: bool = True):
    """Elige el formulario de repuestos más reciente y lo consolida."""
    print("\n" + "=" * 80)
    print("REORGANIZACIÓN ESPECIAL: REPUESTOS FORM")
    print("=" * 80)

    candidates = [
        "templates/taller/repuestos/repuesto_form_final.html",
        "templates/taller/repuestos/repuesto_form_new_clean.html",
        "templates/taller/repuestos/repuesto_form_new.html",
        "templates/taller/repuestos/repuesto_form_limpio.html",
        "templates/taller/repuestos/repuesto_form_clean.html",
    ]

    # Encontrar el más reciente
    latest = None
    latest_time = 0

    for candidate_path in candidates:
        src = BASE_DIR / candidate_path
        if src.exists():
            mtime = src.stat().st_mtime
            if mtime > latest_time:
                latest_time = mtime
                latest = src

    if latest:
        dst = BASE_DIR / "templates/taller/common/repuestos/repuesto_form.html"
        print(f"[INFO] Formulario más reciente: {latest.name}")
        move_file(latest, dst, dry_run)
    else:
        print("[WARN] No se encontró ningún formulario de repuestos candidato")


def reorganize_settings(dry_run: bool = True):
    """Reorganiza settings eligiendo el más completo."""
    print("\n" + "=" * 80)
    print("REORGANIZACIÓN: SETTINGS")
    print("=" * 80)

    # El más completo según el usuario
    src = BASE_DIR / "templates/ejemplos/company_settings_form_unified.html"
    if src.exists():
        dst = BASE_DIR / "templates/settings/company_settings_common.html"
        move_file(src, dst, dry_run)
    else:
        print("[WARN] No se encontró company_settings_form_unified.html")


def main(dry_run: bool = True):
    """Ejecuta la reorganización completa."""
    print("=" * 80)
    print("REORGANIZACIÓN DE TEMPLATES POR MÓDULOS")
    print("=" * 80)
    print(f"Modo: {'DRY-RUN (simulación)' if dry_run else 'EJECUCIÓN REAL'}")
    print(f"Fecha archive: {ARCHIVE_DATE}")
    print("=" * 80)

    # 1. Consolidar COMMON
    consolidate_common(dry_run)

    # 2. Reorganizaciones especiales
    reorganize_repuestos_form(dry_run)
    reorganize_settings(dry_run)

    # 3. Archivar duplicados
    archive_duplicates(dry_run)

    # 4. Mover archivos por país a ubicaciones correctas
    move_country_files_to_correct_location(dry_run)

    # 5. Verificar archivos por país
    verify_country_specific(dry_run)

    print("\n" + "=" * 80)
    print("REORGANIZACIÓN COMPLETADA")
    print("=" * 80)
    if dry_run:
        print("\n[IMPORTANTE] Esto fue una simulación (dry-run).")
        print("Para ejecutar realmente, cambia dry_run=False en main()")


if __name__ == "__main__":
    # PRIMER PASO: ver solo qué haría (sin mover nada)
    # main(dry_run=True)

    # Cuando estés conforme, descomenta la siguiente línea:
    main(dry_run=False)
