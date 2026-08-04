"""
taller/services/workspace_service.py — Workspace UI 2.0

Resolves a WorkspaceDef into a fully-normalized dict ready for template
consumption. Zero ORM queries; all data comes from config fields and the
lazy i18n system.

The resolved dict contract (guaranteed keys):
  brand:
    product_name  str   translated product name
    tagline       str   translated tagline
    icon          str   FontAwesome class
    color_class   str   CSS token
    product_key   str   PRODUCT_* constant
  nav:           list of {key, label, url, icon, is_active}
  widget_keys:   tuple of str
  quick_actions: list of {label, icon, url}
  theme:         dict of CSS custom properties
"""
from __future__ import annotations

from taller.constants.business_modules import ALWAYS_ON, MODULES_BY_RUBRO, NAV_ITEMS, PATH_HINTS
from taller.constants.workspaces import TERMINOLOGY, WorkspaceDef, get_workspace_def


class WorkspaceService:

    @staticmethod
    def get_workspace_def(config) -> WorkspaceDef:
        """Returns the WorkspaceDef for the empresa's rubro. Never None."""
        rubro = None if config is None else (getattr(config, "rubro_principal", None) or "WORKSHOP")
        return get_workspace_def(rubro)

    @staticmethod
    def resolve(
        config,
        url_prefix: str = "/cl/es",
        current_path: str = "",
    ) -> dict:
        """
        Builds the fully-resolved workspace dict. Zero ORM queries.

        Parameters
        ----------
        config:       ConfiguracionEmpresa instance or None
        url_prefix:   country/lang prefix, e.g. "/cl/es"
        current_path: request.path for active-state detection
        """
        ws = WorkspaceService.get_workspace_def(config)
        active = WorkspaceService._active_modules(config)

        return {
            "brand":         WorkspaceService._resolve_brand(ws),
            "nav":           WorkspaceService._resolve_nav(ws, active, url_prefix, current_path),
            "widget_keys":   ws.widget_keys,
            "quick_actions": WorkspaceService._resolve_actions(ws, url_prefix),
            "theme":         ws.theme,
            "product_key":   ws.product_key,
            "texts":         WorkspaceService._resolve_texts(ws),
        }

    # ------------------------------------------------------------------
    # Private helpers — no ORM allowed.
    # ------------------------------------------------------------------

    @staticmethod
    def _term(key: str) -> str:
        """Resolves a terminology key to a translated string."""
        lazy = TERMINOLOGY.get(key)
        return str(lazy) if lazy is not None else key

    @staticmethod
    def _active_modules(config) -> frozenset:
        """Computes active module set from config fields. Zero queries."""
        from taller.constants.business_modules import MOD_VEHICULOS, MOD_SERVICIOS

        if config is None:
            return ALWAYS_ON

        rubro = getattr(config, "rubro_principal", "WORKSHOP") or "WORKSHOP"
        rubros_extra = getattr(config, "rubros", []) or []

        active = set(ALWAYS_ON)
        active |= MODULES_BY_RUBRO.get(rubro, set())
        for r in rubros_extra:
            active |= MODULES_BY_RUBRO.get(r, set())

        if not getattr(config, "usa_vehiculos", True):
            active.discard(MOD_VEHICULOS)
        if not getattr(config, "usa_servicios", True):
            active.discard(MOD_SERVICIOS)

        return frozenset(active)

    @staticmethod
    def _resolve_brand(ws: WorkspaceDef) -> dict:
        return {
            "product_name": WorkspaceService._term(ws.brand.name_key),
            "tagline":      WorkspaceService._term(ws.brand.tagline_key),
            "icon":         ws.brand.icon,
            "color_class":  ws.brand.color_class,
            "product_key":  ws.product_key,
        }

    @staticmethod
    def _resolve_nav(
        ws: WorkspaceDef,
        active: frozenset,
        url_prefix: str,
        current_path: str,
    ) -> list:
        items = []
        seen: set[str] = set()

        for nav_def in ws.nav:
            key = nav_def.module_key
            if key not in active:
                continue
            seen.add(key)
            base = NAV_ITEMS[key]
            hint = PATH_HINTS.get(key, "")
            items.append({
                "key":       key,
                "label":     WorkspaceService._term(nav_def.term_key),
                "url":       f"{url_prefix}/{base['path']}",
                "icon":      nav_def.icon,
                "is_active": bool(hint and hint in current_path),
            })

        # Append active modules not covered by this workspace nav (safety net)
        for key in sorted(active - seen, key=lambda k: NAV_ITEMS[k]["order"]):
            defn = NAV_ITEMS[key]
            hint = PATH_HINTS.get(key, "")
            items.append({
                "key":       key,
                "label":     defn["label"],
                "url":       f"{url_prefix}/{defn['path']}",
                "icon":      defn["icon"],
                "is_active": bool(hint and hint in current_path),
            })

        return items

    @staticmethod
    def _resolve_actions(ws: WorkspaceDef, url_prefix: str) -> list:
        return [
            {
                "label": WorkspaceService._term(action.term_key),
                "icon":  action.icon,
                "url":   f"{url_prefix}/{action.path}",
            }
            for action in ws.quick_actions
        ]

    @staticmethod
    def _resolve_texts(ws: WorkspaceDef) -> dict:
        t = ws.texts
        return {
            "search_title":        WorkspaceService._term(t.search_title_key),
            "search_label":        WorkspaceService._term(t.search_label_key),
            "search_placeholder":  WorkspaceService._term(t.search_placeholder_key),
            "search_hint":         WorkspaceService._term(t.search_hint_key),
            "live_feed_title":     WorkspaceService._term(t.live_feed_title_key),
            "live_feed_metric":    WorkspaceService._term(t.live_feed_metric_key),
            "quick_actions_label": WorkspaceService._term(t.quick_actions_label_key),
            "activity_feed_title": WorkspaceService._term(t.activity_feed_title_key),
        }
