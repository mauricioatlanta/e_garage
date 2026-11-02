# -*- coding: utf-8 -*-
"""
Backfill seguro y reversible de PiezaDesarmeName (i18n) para piezas existentes.

Orden de matching a catálogo USA:
1) código exacto (pieza.codigo == usa.codigo)
2) nombre_es exacto normalizado
3) aliases_es normalizados
4) mapa manual legacy -> código USA
5) sin match: no crea en inglés
"""
import unicodedata

from django.core.management.base import BaseCommand
from django.db import transaction

from taller.models.pieza_desarme import PiezaDesarme, PiezaDesarmeName

# Equivalencias explícitas de nombres legacy de desarme hacia códigos USA.
# Claves y valores en formato normalizado (sin tildes, minúsculas).
LEGACY_TO_USA_EQUIVALENCES = {
    "tapa de cilindros": "cylinder_head",
    "culata": "cylinder_head",
    "capot": "hood",
    "capo": "hood",
    "puerta delantera izq": "door",
    "puerta delantera der": "door",
    "puerta trasera izq": "door",
    "puerta trasera der": "door",
    "guardabarros izq": "fender",
    "guardabarros der": "fender",
    "guardabarro izq": "fender",
    "guardabarro der": "fender",
    "múltiple admisión": "intake_manifold",
    "multiple admision": "intake_manifold",
    "múltiple de admisión": "intake_manifold",
    "múltiple escape": "exhaust_manifold",
    "multiple escape": "exhaust_manifold",
    "múltiple de escape": "exhaust_manifold",
    "tapa baul": "trunk_lid",
    "tapa de baul": "trunk_lid",
    "puerta maletero": "liftgate",
    "baguetera": "liftgate",
    "espejo retrovisor izq": "side_mirror",
    "espejo retrovisor der": "side_mirror",
    "retrovisor": "side_mirror",
    "volante": "steering_wheel",
    "tablero completo": "dashboard",
    "consola central": "center_console",
    "asiento delantero izq": "seat",
    "asiento delantero der": "seat",
    "asiento trasero": "seat",
    "airbag conductor": "airbag",
    "airbag pasajero": "airbag",
    # Engine / fuel
    "distribuidor": "distributor",
    "turbo": "turbocharger",
    "intercooler": "intercooler",
    "bomba inyectora": "injection_pump",
    "inyectores (set)": "fuel_injector_set",
    "inyectores set": "fuel_injector_set",
    "inyectores": "fuel_injector_set",
    # Body / interior
    "tapa de bencinera": "fuel_filler_door",
    "tapa bencinera": "fuel_filler_door",
    "palanca de cambios": "gear_shifter",
    "alfombra delantera": "front_floor_mat",
    "alfombra trasera": "rear_floor_mat",
    "retrovisor interior": "rear_view_mirror_inner",
    "tapacubos volante": "steering_wheel_hub_cap",
    "cinturones de seguridad (set)": "seat_belt_set",
    "cinturones de seguridad": "seat_belt_set",
    # Suspension / steering
    "amortiguador delantero izq": "front_shock_left",
    "amortiguador delantero izquierdo": "front_shock_left",
    "amortiguador delantero der": "front_shock_right",
    "amortiguador delantero derecho": "front_shock_right",
    "amortiguador trasero izq": "rear_shock_left",
    "amortiguador trasero izquierdo": "rear_shock_left",
    "amortiguador trasero der": "rear_shock_right",
    "amortiguador trasero derecho": "rear_shock_right",
    "resorte delantero (par)": "front_spring_pair",
    "resorte delantero par": "front_spring_pair",
    "resorte trasero (par)": "rear_spring_pair",
    "resorte trasero par": "rear_spring_pair",
    "brazo inferior izq": "lower_control_arm_left",
    "brazo inferior izquierdo": "lower_control_arm_left",
    "brazo inferior der": "lower_control_arm_right",
    "brazo inferior derecho": "lower_control_arm_right",
    "rotula direccion izq": "tie_rod_end_left",
    "rotula direccion izquierdo": "tie_rod_end_left",
    "rotula direccion der": "tie_rod_end_right",
    "rotula direccion derecho": "tie_rod_end_right",
    "maza delantera izq": "front_hub_left",
    "masa delantera izq": "front_hub_left",
    "maza delantera der": "front_hub_right",
    "masa delantera der": "front_hub_right",
    "direccion hidraulica": "power_steering_pump",
    "cremallera": "steering_rack",
    # Lighting
    "faro izquierdo": "headlight_left",
    "faro derecho": "headlight_right",
    "luz trasera izq": "tail_light_left",
    "luz trasera der": "tail_light_right",
    "luz de neblina izq": "fog_light_left",
    "luz de neblina der": "fog_light_right",
    "luz de techo": "dome_light",
    "intermitente izq": "turn_signal_left",
    "intermitente der": "turn_signal_right",
    "luz de placa": "license_plate_light",
    "faro trasero izq": "rear_lamp_left",
    "faro trasero der": "rear_lamp_right",
    # Electronics
    "radio": "radio_unit",
    "ecu / computadora": "ecu_computer",
    "ecu computadora": "ecu_computer",
    "sensores abs": "abs_sensor_set",
    "ventana delantera izq": "front_window_left",
    "ventana delantera der": "front_window_right",
    "ventana trasera izq": "rear_window_left",
    "ventana trasera der": "rear_window_right",
    "motor elevavidrios izq": "window_regulator_motor_left",
    "motor elevavidrios der": "window_regulator_motor_right",
    "sensores srs": "srs_sensor_set",
    "fusibles y relay (set)": "fuse_relay_set",
    "fusibles y relay set": "fuse_relay_set",
    "cableado principal": "main_wiring_harness",
    "bomba combustible": "fuel_pump",
    "bomba de combustible": "fuel_pump",
    "estarter": "starter",
    # Exhaust
    "convertidor catalitico": "catalytic_converter",
    "sonda lambda": "oxygen_sensor",
    "mofle central": "center_muffler",
    "mofle trasero": "rear_muffler",
    "cano escape completo": "exhaust_pipe_complete",
    "caño escape completo": "exhaust_pipe_complete",
    "flexible escape": "flex_exhaust_pipe",
    "soporte escape": "exhaust_hanger",
    "tapon escape": "exhaust_end_cap",
    "tapon de escape": "exhaust_end_cap",
    # Wheels / brakes
    "rueda 15": "wheel_15",
    'rueda 15"': "wheel_15",
    "rueda 16": "wheel_16",
    'rueda 16"': "wheel_16",
    "rueda 17": "wheel_17",
    'rueda 17"': "wheel_17",
    "disco freno delantero (par)": "front_brake_disc_pair",
    "disco freno trasero (par)": "rear_brake_disc_pair",
    "tambor freno trasero (par)": "rear_brake_drum_pair",
    "pinza freno delantera izq": "front_brake_caliper_left",
    "pinza freno delantera der": "front_brake_caliper_right",
    "pastillas freno (set)": "brake_pads_set",
    "pastillas de freno (set)": "brake_pads_set",
    "tambor (unidad)": "brake_drum_unit",
    "tambor unidad": "brake_drum_unit",
}


def _norm(value):
    """Normaliza string para comparación robusta."""
    s = (value or "").strip().lower()
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return " ".join(s.split())


def _build_usa_catalog_indexes():
    """
    Crea índices de catálogo USA:
    - by_codigo
    - by_nombre_es_norm
    - by_alias_es_norm
    """
    from taller.catalogos.catalogo_piezas_desarme_usa import CATALOGO_PIEZAS_DESARME_USA

    by_codigo = {}
    by_nombre_es_norm = {}
    by_alias_es_norm = {}

    for p in CATALOGO_PIEZAS_DESARME_USA:
        codigo = _norm(p.get("codigo"))
        if not codigo:
            continue
        nombre_en = (
            p.get("nombre_en_oficial") or p.get("nombre_en_slang") or p.get("codigo") or ""
        ).strip()
        aliases_en = [str(a).strip() for a in (p.get("sinonimos_en") or []) if str(a).strip()]
        entry = {
            "codigo": codigo,
            "nombre_en": nombre_en,
            "aliases_en": aliases_en[:20],
            "nombre_es": (p.get("nombre_es") or "").strip(),
        }
        by_codigo[codigo] = entry

        nombre_es_norm = _norm(p.get("nombre_es"))
        if nombre_es_norm and nombre_es_norm not in by_nombre_es_norm:
            by_nombre_es_norm[nombre_es_norm] = entry

        for alias_es in p.get("sinonimos_es") or []:
            alias_norm = _norm(alias_es)
            if alias_norm and alias_norm not in by_alias_es_norm:
                by_alias_es_norm[alias_norm] = entry

    return by_codigo, by_nombre_es_norm, by_alias_es_norm


def _find_match_for_piece(pieza, by_codigo, by_nombre_es_norm, by_alias_es_norm):
    """Busca match de una pieza siguiendo el orden definido."""
    codigo_norm = _norm(pieza.codigo)
    nombre_norm = _norm(pieza.nombre)

    # 1) código exacto
    if codigo_norm and codigo_norm in by_codigo:
        return by_codigo[codigo_norm], "codigo_exacto"

    # 2) nombre_es exacto normalizado
    if nombre_norm and nombre_norm in by_nombre_es_norm:
        return by_nombre_es_norm[nombre_norm], "nombre_es_exacto"

    # 3) aliases_es normalizados
    if nombre_norm and nombre_norm in by_alias_es_norm:
        return by_alias_es_norm[nombre_norm], "alias_es"

    # 4) mapa manual legacy -> código USA
    mapped_codigo = LEGACY_TO_USA_EQUIVALENCES.get(nombre_norm)
    if mapped_codigo:
        mapped_codigo_norm = _norm(mapped_codigo)
        entry = by_codigo.get(mapped_codigo_norm)
        if entry:
            return entry, "equivalencia_manual"

    return None, None


class Command(BaseCommand):
    help = "Backfill PiezaDesarmeName (es/en) con matching semántico legacy->USA. Usar --dry-run primero."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run", action="store_true", help="Solo reportar, sin guardar cambios."
        )
        parser.add_argument(
            "--batch", type=int, default=5000, help="Procesar en lotes de N piezas."
        )

    def handle(self, *args, **options):
        dry_run = options.get("dry_run", False)
        batch_size = max(1, options.get("batch", 5000))

        if dry_run:
            self.stdout.write(self.style.WARNING("[DRY RUN] No se guardarán cambios.\n"))

        self.stdout.write("Backfill PiezaDesarmeName (es / en con matching semántico)\n")
        self.stdout.write("=" * 70 + "\n")

        by_codigo, by_nombre_es_norm, by_alias_es_norm = _build_usa_catalog_indexes()
        self.stdout.write(f"Catálogo USA por código: {len(by_codigo)}")
        self.stdout.write(f"Índice nombre_es: {len(by_nombre_es_norm)}")
        self.stdout.write(f"Índice aliases_es: {len(by_alias_es_norm)}")
        self.stdout.write(f"Equivalencias manuales: {len(LEGACY_TO_USA_EQUIVALENCES)}\n")

        created_es = 0
        created_en = 0
        skipped_es = 0
        skipped_en = 0
        no_match_en = 0
        conflicts = 0

        match_stats = {
            "codigo_exacto": 0,
            "nombre_es_exacto": 0,
            "alias_es": 0,
            "equivalencia_manual": 0,
        }

        qs = PiezaDesarme.objects.prefetch_related("names").order_by("id")
        total = qs.count()
        self.stdout.write(f"Piezas a revisar: {total}\n")

        processed = 0
        for offset in range(0, total, batch_size):
            batch = list(qs[offset : offset + batch_size])
            to_create_es = []
            to_create_en = []

            for pieza in batch:
                names_es = [n for n in pieza.names.all() if n.language == "es"]
                names_en = [n for n in pieza.names.all() if n.language == "en"]

                if not names_es:
                    label_es = (pieza.nombre or "").strip() or pieza.codigo or "Sin nombre"
                    to_create_es.append(
                        PiezaDesarmeName(
                            pieza_desarme=pieza,
                            language="es",
                            label=label_es[:255],
                            aliases=[],
                            is_default=True,
                        )
                    )
                else:
                    skipped_es += 1

                if names_en:
                    skipped_en += 1
                    continue

                entry, strategy = _find_match_for_piece(
                    pieza=pieza,
                    by_codigo=by_codigo,
                    by_nombre_es_norm=by_nombre_es_norm,
                    by_alias_es_norm=by_alias_es_norm,
                )
                if entry and entry.get("nombre_en"):
                    to_create_en.append(
                        PiezaDesarmeName(
                            pieza_desarme=pieza,
                            language="en",
                            label=entry["nombre_en"][:255],
                            aliases=(entry.get("aliases_en") or [])[:20],
                            is_default=True,
                        )
                    )
                    if strategy in match_stats:
                        match_stats[strategy] += 1
                else:
                    no_match_en += 1

            if not dry_run:
                with transaction.atomic():
                    for obj in to_create_es:
                        try:
                            obj.save()
                            created_es += 1
                        except Exception as e:
                            conflicts += 1
                            if conflicts <= 5:
                                self.stdout.write(
                                    self.style.ERROR(
                                        f"  Conflicto es: pieza_id={obj.pieza_desarme_id} {e}"
                                    )
                                )
                    for obj in to_create_en:
                        try:
                            obj.save()
                            created_en += 1
                        except Exception as e:
                            conflicts += 1
                            if conflicts <= 5:
                                self.stdout.write(
                                    self.style.ERROR(
                                        f"  Conflicto en: pieza_id={obj.pieza_desarme_id} {e}"
                                    )
                                )
            else:
                created_es += len(to_create_es)
                created_en += len(to_create_en)

            processed += len(batch)
            if processed % 1000 == 0 and processed > 0:
                self.stdout.write(f"  Procesadas {processed}/{total} piezas...")

        self.stdout.write("\n" + "=" * 70)
        self.stdout.write("Resumen:")
        self.stdout.write(f"  Creados (es):  {created_es}")
        self.stdout.write(f"  Creados (en):  {created_en}")
        self.stdout.write(f"  Omitidos (ya tenían es): {skipped_es}")
        self.stdout.write(f"  Omitidos (ya tenían en): {skipped_en}")
        self.stdout.write(f"  Sin match en catálogo para 'en': {no_match_en}")
        self.stdout.write(f"  Conflictos al guardar: {conflicts}")
        self.stdout.write("  Match por estrategia:")
        self.stdout.write(f"    - código exacto: {match_stats['codigo_exacto']}")
        self.stdout.write(f"    - nombre_es exacto: {match_stats['nombre_es_exacto']}")
        self.stdout.write(f"    - alias_es: {match_stats['alias_es']}")
        self.stdout.write(f"    - equivalencia manual: {match_stats['equivalencia_manual']}")
        if dry_run:
            self.stdout.write(
                self.style.WARNING("\n[DRY RUN] Ejecuta sin --dry-run para aplicar cambios.")
            )
