"""
Vistas de autocomplete para colores de cliente
Sigue la misma dinámica que el sistema de colores de vehículos
"""

import dal.autocomplete
from django.db.models import Q

from taller.models.color_cliente import ColorCliente


class ColorClienteAutocomplete(dal.autocomplete.Select2QuerySetView):
    """Autocomplete para colores de cliente filtrado por país"""

    def get_queryset(self):
        # Obtener el país del usuario desde la empresa
        pais = None
        if hasattr(self.request.user, "empresa") and self.request.user.empresa:
            pais = getattr(self.request.user.empresa, "pais", None)

        # Si no hay país, usar Chile por defecto
        if not pais:
            pais = "CL"

        # Obtener colores para el país específico
        qs = ColorCliente.get_colores_para_pais(pais)

        # Filtrar por búsqueda si existe
        if self.q:
            qs = qs.filter(
                Q(nombre__icontains=self.q) | Q(codigo_color__icontains=self.q)
            )

        return qs.order_by("orden", "nombre")

    def get_result_label(self, result):
        """Personalizar la etiqueta del resultado para mostrar el color"""
        return f"<span style='color: {result.codigo_color};'>{result.nombre}</span>"

    def get_result_value(self, result):
        """Valor que se guarda en el formulario"""
        return result.pk
