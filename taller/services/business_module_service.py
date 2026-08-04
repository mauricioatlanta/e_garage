"""
BusinessModuleService — resuelve los módulos de navegación activos para una empresa.

Deriva el conjunto de módulos desde ConfiguracionEmpresa.rubro_principal y
ConfiguracionEmpresa.rubros, respetando los flags usa_vehiculos / usa_servicios.
La navegación final usa el perfil de producto para reordenar y renombrar ítems.
No modifica la base de datos salvo en mark_modules_configured().
"""

from taller.constants.business_modules import (
    ALWAYS_ON,
    MODULES_BY_RUBRO,
    NAV_ITEMS,
    PATH_HINTS,
    MOD_VEHICULOS,
    MOD_SERVICIOS,
    MOD_DESARME,
)


class BusinessModuleService:

    @staticmethod
    def get_active_modules(config) -> frozenset:
        """Devuelve el conjunto de claves de módulos activos para la config dada."""
        if config is None:
            return ALWAYS_ON

        rubro = getattr(config, "rubro_principal", "WORKSHOP") or "WORKSHOP"
        rubros_extra = getattr(config, "rubros", []) or []

        active = set(ALWAYS_ON)
        active |= MODULES_BY_RUBRO.get(rubro, set())
        for r in rubros_extra:
            active |= MODULES_BY_RUBRO.get(r, set())

        # Respetar flags explícitos del modelo
        if not getattr(config, "usa_vehiculos", True):
            active.discard(MOD_VEHICULOS)
        if not getattr(config, "usa_servicios", True):
            active.discard(MOD_SERVICIOS)

        return frozenset(active)

    @staticmethod
    def get_product_profile(config) -> dict:
        """
        Devuelve el perfil de producto correspondiente al rubro_principal.

        El perfil define nombre, tagline, orden de navegación, labels/iconos
        específicos por producto, KPIs y accesos rápidos del dashboard.
        Nunca retorna None; usa PRODUCT_TALLER como fallback.
        """
        from taller.constants.product_profiles import (
            DEFAULT_PRODUCT,
            PRODUCT_PROFILES,
            RUBRO_TO_PRODUCT,
        )
        rubro = "WORKSHOP" if config is None else (getattr(config, "rubro_principal", "WORKSHOP") or "WORKSHOP")
        product_key = RUBRO_TO_PRODUCT.get(rubro, DEFAULT_PRODUCT)
        return PRODUCT_PROFILES[product_key]

    @staticmethod
    def get_nav_items(config, url_prefix: str = "/cl/es", current_path: str = "") -> list:
        """
        Devuelve lista ordenada de dicts de navegación para los módulos activos.

        El orden, labels e iconos provienen del perfil de producto del rubro.
        Los módulos activos que no aparezcan en el perfil se añaden al final
        usando los defaults de NAV_ITEMS, para no perder funcionalidad futura.

        Cada dict tiene: key, label, url, icon, is_active.
        """
        active = BusinessModuleService.get_active_modules(config)
        profile = BusinessModuleService.get_product_profile(config)
        profile_nav = profile.get("nav", [])

        items = []
        seen = set()

        for nav_def in profile_nav:
            key = nav_def["key"]
            if key not in active:
                continue
            seen.add(key)
            base = NAV_ITEMS[key]
            hint = PATH_HINTS.get(key, "")
            items.append({
                "key": key,
                "label": nav_def["label"],
                "url": f"{url_prefix}/{base['path']}",
                "icon": nav_def["icon"],
                "is_active": bool(hint and hint in current_path),
            })

        # Append any active modules not covered by the profile (future-proofing)
        for key in sorted(active - seen, key=lambda k: NAV_ITEMS[k]["order"]):
            defn = NAV_ITEMS[key]
            hint = PATH_HINTS.get(key, "")
            items.append({
                "key": key,
                "label": defn["label"],
                "url": f"{url_prefix}/{defn['path']}",
                "icon": defn["icon"],
                "is_active": bool(hint and hint in current_path),
            })

        return items

    @staticmethod
    def needs_module_configuration(empresa) -> bool:
        """
        True si la empresa completó el onboarding pero aún no configuró módulos.
        Se usa para mostrar el asistente de migración una sola vez.
        """
        if not getattr(empresa, "onboarding_completado", False):
            return False
        config = getattr(empresa, "config", None)
        if config is None:
            return False
        return getattr(config, "modules_configured_at", None) is None

    @staticmethod
    def mark_modules_configured(config) -> None:
        """Registra la fecha/hora en que el usuario configuró sus módulos."""
        from django.utils import timezone
        config.modules_configured_at = timezone.now()
        config.save(update_fields=["modules_configured_at"])

    @staticmethod
    def infer_suggestions(empresa) -> list:
        """
        Sugiere módulos adicionales detectando evidencia en datos existentes.
        Útil para el asistente de migración de empresas existentes.
        """
        suggestions = []
        try:
            if empresa.pieza_set.exists():
                suggestions.append(MOD_DESARME)
        except Exception:
            pass
        return suggestions
