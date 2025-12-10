"""
Configuración centralizada para eGarage
"""

from .country_settings import (
    CountrySettings,
    build_country_url,
    get_country_config,
    get_country_from_url,
    get_url_prefix,
    is_country_valid,
)
from .rubros import (
    RUBROS_TALLER,
    RUBROS_DICT,
    get_rubro_label,
    get_rubros_list,
)
from .rubros_translations import (
    RUBROS_BY_COUNTRY,
    get_rubros_translated,
    get_rubro_label as get_rubro_label_by_country,
    get_rubros_choices_for_country,
)

__all__ = [
    "CountrySettings",
    "get_country_config",
    "get_url_prefix",
    "get_country_from_url",
    "build_country_url",
    "is_country_valid",
    "RUBROS_TALLER",
    "RUBROS_DICT",
    "get_rubro_label",
    "get_rubros_list",
    "RUBROS_BY_COUNTRY",
    "get_rubros_translated",
    "get_rubro_label_by_country",
    "get_rubros_choices_for_country",
]
