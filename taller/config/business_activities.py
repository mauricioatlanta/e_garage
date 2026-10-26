"""Canonical business-activity groups used by signup and company settings."""

ACTIVITY_GROUPS = (
    {"key": "TALLER_MECANICO", "label": "Taller Mecánico", "label_en": "Auto Repair Shop", "description": "Autos, motos, camiones — reparación y mantención", "description_en": "Cars, motorcycles, trucks — repair and maintenance", "icon": "🔧", "rubros": ("WORKSHOP", "WORKSHOP_MOTO", "WORKSHOP_HEAVY")},
    {"key": "CASA_REPUESTOS", "label": "Casa de Repuestos", "label_en": "Auto Parts Store", "description": "Venta de partes y repuestos automotrices", "description_en": "Auto parts and accessories sales", "icon": "📦", "rubros": ("PARTS",)},
    {"key": "DESARMADURIA", "label": "Desarmaduría / Salvage", "label_en": "Salvage Yard / Dismantler", "description": "Desarme de vehículos, venta de piezas desmontadas", "description_en": "Vehicle dismantling and used parts sales", "icon": "🔩", "rubros": ("DESARMADURIA",)},
    {"key": "NEUMATICOS", "label": "Neumáticos / Vulcanización", "label_en": "Tires / Wheel Shop", "description": "Venta e instalación de neumáticos y llantas", "description_en": "Tire and wheel sales and installation", "icon": "⭕", "rubros": ("TIRE",)},
    {"key": "CARROCERIA_DETAILING", "label": "Carrocería / Pintura / Detailing", "label_en": "Body Shop / Detailing", "description": "Reparación de chapa, pintura, lavado y estética", "description_en": "Bodywork, paint, wash and detailing", "icon": "🎨", "rubros": ("BODYSHOP", "DETAILING")},
    {"key": "RECICLAJE", "label": "Reciclaje", "label_en": "Recycling", "description": "Compra y reventa de catalíticos y chatarra electrónica", "description_en": "Catalytic converter and e-scrap buying and resale", "icon": "♻️", "rubros": ("RECYCLING",)},
    {"key": "ESPECIALISTA", "label": "Especialista", "label_en": "Specialist", "description": "Electricidad, escapes, suspensión, audio u otra especialidad", "description_en": "Electrical, exhaust, suspension, audio or other specialty", "icon": "⚡", "rubros": ("ELECTRIC", "EXHAUST", "SUSPENSION_STEERING", "GLASS_AUDIO", "BRAKES")},
    {"key": "OTRO", "label": "Otro / Mixto", "label_en": "Other / Mixed", "description": "Negocio no listado o con múltiples giros", "description_en": "Unlisted business or multiple services", "icon": "⊞", "rubros": ("MIXED",)},
    {"key": "GRUAS", "label": "Grúas y asistencia vial", "label_en": "Towing and roadside assistance", "description": "Traslado, rescate y asistencia de vehículos", "description_en": "Vehicle towing, recovery and roadside assistance", "icon": "🚛", "rubros": ("TOWING",)},
)

GROUP_TO_RUBROS = {group["key"]: group["rubros"] for group in ACTIVITY_GROUPS}
GROUP_CHOICES = tuple((group["key"], group["label"]) for group in ACTIVITY_GROUPS)
VALID_GROUP_KEYS = frozenset(GROUP_TO_RUBROS)
VALID_RUBRO_CODES = frozenset(code for codes in GROUP_TO_RUBROS.values() for code in codes)


def expand_activity_groups(primary_group: str, additional_groups=()) -> list[str]:
    """Expand UI groups into ordered, unique rubro codes."""
    if primary_group not in VALID_GROUP_KEYS:
        raise ValueError("Actividad principal no válida.")

    ordered_groups = [primary_group]
    for group in additional_groups:
        if group not in VALID_GROUP_KEYS:
            raise ValueError("Actividad adicional no válida.")
        if group not in ordered_groups:
            ordered_groups.append(group)

    rubros: list[str] = []
    for group in ordered_groups:
        for rubro in GROUP_TO_RUBROS[group]:
            if rubro not in rubros:
                rubros.append(rubro)
    return rubros


def groups_for_rubros(rubro_principal: str, rubros) -> tuple[str, list[str]]:
    """Return the best UI group representation for an existing configuration."""
    effective = [rubro_principal] + [r for r in (rubros or []) if r != rubro_principal]
    selected = []
    for group in ACTIVITY_GROUPS:
        codes = group["rubros"]
        if rubro_principal in codes or all(code in effective for code in codes):
            selected.append(group["key"])

    primary = next(
        (group["key"] for group in ACTIVITY_GROUPS if rubro_principal in group["rubros"]),
        "OTRO",
    )
    return primary, [group for group in selected if group != primary]
