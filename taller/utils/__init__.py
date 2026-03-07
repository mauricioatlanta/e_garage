# Utilidades centralizadas para el sistema
# Re-export para que "from taller.utils import get_normalized_country" funcione
# (el package taller/utils/ shadowea el archivo taller/utils.py)
from taller.utils.country import get_normalized_country, get_country_from_request

__all__ = ["get_normalized_country", "get_country_from_request"]
