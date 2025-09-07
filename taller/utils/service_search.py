"""
Utilidades para búsqueda y manejo de servicios multilenguaje
Incluye normalización, búsqueda por aliases y fuzzy matching
"""

import json
import re
from difflib import SequenceMatcher

from django.db.models import Q
from django.utils.text import slugify

from taller.servicios.models import (CategoriaServicio, CategoriaServicioName,
                                     Servicio, ServicioName,
                                     SubcategoriaServicio,
                                     SubcategoriaServicioName)


def normalize_search_term(term):
    """
    Normaliza término de búsqueda removiendo acentos, mayúsculas y stopwords
    """
    if not term:
        return ""

    # Convertir a lowercase y remover caracteres especiales
    normalized = re.sub(r"[^\w\s]", " ", term.lower())

    # Remover stopwords comunes
    stopwords = {"de", "del", "la", "el", "en", "y", "a", "con", "para", "por"}
    words = [
        word for word in normalized.split() if word not in stopwords and len(word) > 1
    ]

    return " ".join(words)


def calculate_similarity(term1, term2):
    """Calcula similitud entre dos términos usando SequenceMatcher"""
    return SequenceMatcher(None, term1.lower(), term2.lower()).ratio()


class ServiceSearchEngine:
    """
    Motor de búsqueda avanzado para servicios con soporte multilenguaje
    """

    def __init__(self, country="CL", language="es"):
        self.country = country
        self.language = language

    def search_services(self, query, limit=10):
        """
        Busca servicios por término con scoring y ranking

        Args:
            query (str): Término de búsqueda
            limit (int): Máximo número de resultados

        Returns:
            list: Lista de servicios ordenados por relevancia
        """
        if not query or len(query.strip()) < 2:
            return []

        normalized_query = normalize_search_term(query)
        results = []

        # 1. Búsqueda exacta en labels
        exact_matches = self._search_exact_labels(normalized_query)
        results.extend([(service, 100) for service in exact_matches])

        # 2. Búsqueda por prefijo en labels
        prefix_matches = self._search_prefix_labels(normalized_query)
        results.extend(
            [
                (service, 80)
                for service in prefix_matches
                if service not in [r[0] for r in results]
            ]
        )

        # 3. Búsqueda en aliases
        alias_matches = self._search_aliases(normalized_query)
        results.extend(
            [
                (service, 70)
                for service in alias_matches
                if service not in [r[0] for r in results]
            ]
        )

        # 4. Búsqueda fuzzy
        fuzzy_matches = self._search_fuzzy(normalized_query)
        results.extend(
            [
                (service, score)
                for service, score in fuzzy_matches
                if service not in [r[0] for r in results]
            ]
        )

        # Ordenar por score y limitar
        results.sort(key=lambda x: x[1], reverse=True)

        return [result[0] for result in results[:limit]]

    def _search_exact_labels(self, query):
        """Búsqueda exacta en nombres principales"""
        return Servicio.objects.filter(
            country=self.country,
            activo=True,
            names__language=self.language,
            names__label__iexact=query,
        ).distinct()

    def _search_prefix_labels(self, query):
        """Búsqueda por prefijo en nombres principales"""
        return Servicio.objects.filter(
            country=self.country,
            activo=True,
            names__language=self.language,
            names__label__istartswith=query,
        ).distinct()

    def _search_aliases(self, query):
        """Búsqueda en aliases/sinónimos"""
        # Buscar en JSON aliases - requiere raw SQL o postgre specific lookups
        services = []

        service_names = ServicioName.objects.filter(
            servicio__country=self.country,
            servicio__activo=True,
            language=self.language,
        ).select_related("servicio")

        for service_name in service_names:
            aliases = service_name.aliases or []
            for alias in aliases:
                if normalize_search_term(alias) == query:
                    services.append(service_name.servicio)
                    break

        return list(set(services))

    def _search_fuzzy(self, query, min_similarity=0.6):
        """Búsqueda fuzzy con threshold mínimo"""
        services_with_scores = []

        service_names = ServicioName.objects.filter(
            servicio__country=self.country,
            servicio__activo=True,
            language=self.language,
        ).select_related("servicio")

        for service_name in service_names:
            # Comparar con label principal
            similarity = calculate_similarity(
                query, normalize_search_term(service_name.label)
            )
            if similarity >= min_similarity:
                services_with_scores.append(
                    (service_name.servicio, int(similarity * 60))
                )  # Max score 60 for fuzzy

            # Comparar con aliases
            aliases = service_name.aliases or []
            for alias in aliases:
                similarity = calculate_similarity(query, normalize_search_term(alias))
                if similarity >= min_similarity:
                    services_with_scores.append(
                        (service_name.servicio, int(similarity * 55))
                    )  # Max score 55 for fuzzy alias
                    break

        return services_with_scores

    def search_categories(self, query, limit=5):
        """Busca categorías por término"""
        if not query or len(query.strip()) < 2:
            return []

        normalized_query = normalize_search_term(query)

        return CategoriaServicio.objects.filter(
            country=self.country,
            names__language=self.language,
            names__label__icontains=normalized_query,
        ).distinct()[:limit]


def get_service_autocomplete_data(country="CL", language="es", category_id=None):
    """
    Genera datos para autocompletado de servicios

    Args:
        country (str): País ('CL', 'US')
        language (str): Idioma ('es', 'en')
        category_id (int): ID de categoría (opcional)

    Returns:
        list: Lista de diccionarios con datos de servicios
    """
    queryset = Servicio.objects.filter(country=country, activo=True).select_related(
        "subcategoria__categoria"
    )

    if category_id:
        queryset = queryset.filter(subcategoria__categoria_id=category_id)

    services_data = []

    for service in queryset:
        # Obtener nombre localizado
        label = service.get_label(language)

        # Obtener aliases para búsqueda
        try:
            service_name = service.names.get(language=language, is_default=True)
            aliases = service_name.aliases or []
        except ServicioName.DoesNotExist:
            aliases = []

        services_data.append(
            {
                "id": service.id,
                "code": service.code,
                "label": label,
                "aliases": aliases,
                "category": service.subcategoria.categoria.get_label(language),
                "subcategory": service.subcategoria.get_label(language),
                "precio_base": (
                    float(service.precio_base) if service.precio_base else None
                ),
            }
        )

    return services_data


def qs_for_country(queryset, request):
    """
    Helper para filtrar querysets por país del request
    Evita repetir .filter(country=request.country) en todos lados
    """
    country = getattr(request, "country", "CL")
    return queryset.filter(country=country)
