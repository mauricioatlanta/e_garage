"""
Vistas de autocompletado para formularios de vehículos
Usando Django Autocomplete Light (DAL) para búsqueda inteligente
"""

import logging

from dal import autocomplete

from django.db.models import Q, Value, CharField
from django.db.models.functions import Coalesce, Concat

from taller.models.clientes import Cliente
from taller.models.extras_vehiculo import (
    CajaVehiculo,
    CajaVehiculoEmpresa,
    MotorVehiculo,
    MotorVehiculoEmpresa,
)
from taller.models.modelo import Modelo

logger = logging.getLogger(__name__)


class ClienteAutocomplete(autocomplete.Select2QuerySetView):
    """
    Autocompletado inteligente para clientes
    Búsqueda por: nombre, apellido, nombre completo, email, teléfono, tax_id
    Filtrado por empresa del usuario
    """

    def get_queryset(self):
        """Base queryset filtrado por empresa del usuario"""
        if not self.request.user.is_authenticated:
            logger.warning("[ClienteAutocomplete] Usuario no autenticado")
            return Cliente.objects.none()

        # Obtener empresa del usuario
        empresa = getattr(self.request.user, "empresa", None)
        if not empresa:
            logger.warning(
                f"[ClienteAutocomplete] Usuario {self.request.user.username} no tiene empresa asignada"
            )
            return Cliente.objects.none()

        logger.info(
            f"[ClienteAutocomplete] Buscando clientes para empresa: {empresa.id} ({empresa.nombre_taller if hasattr(empresa, 'nombre_taller') else 'N/A'})"
        )

        # Base queryset filtrado por empresa
        qs = Cliente.objects.filter(empresa=empresa).order_by("nombre", "apellido")

        # Contar total de clientes antes de filtrar
        total_clientes = qs.count()
        logger.info(f"[ClienteAutocomplete] Total de clientes en empresa: {total_clientes}")

        # Si hay término de búsqueda, filtrar
        if self.q:
            query_term = self.q.strip()
            logger.info(f"[ClienteAutocomplete] Búsqueda con término: '{query_term}'")

            # Annotar con nombre completo para búsqueda mejorada
            # Usar Coalesce para manejar apellidos nulos
            qs = qs.annotate(
                nombre_completo=Concat(
                    "nombre", Value(" "), Coalesce("apellido", Value("")), output_field=CharField()
                )
            )

            # Búsqueda case-insensitive en múltiples campos incluyendo nombre completo
            qs = qs.filter(
                Q(nombre__icontains=query_term)
                | Q(apellido__icontains=query_term)
                | Q(nombre_completo__icontains=query_term)  # Búsqueda en nombre completo
                | Q(email__icontains=query_term)
                | Q(telefono__icontains=query_term)
                | Q(tax_id__icontains=query_term)
            ).distinct()

            resultados_count = qs.count()
            logger.info(f"[ClienteAutocomplete] Resultados encontrados: {resultados_count}")

            if resultados_count > 0:
                # Log de los primeros resultados para debugging
                primeros = list(qs[:5])
                for cliente in primeros:
                    logger.info(
                        f"[ClienteAutocomplete] ✅ Resultado: {cliente.nombre} {cliente.apellido or ''} (ID: {cliente.id})"
                    )
            else:
                logger.warning(
                    f"[ClienteAutocomplete] ⚠️ No se encontraron resultados para '{query_term}'"
                )
                # Debug: mostrar todos los clientes disponibles para ayudar a diagnosticar
                todos = Cliente.objects.filter(empresa=empresa).values_list(
                    "id", "nombre", "apellido"
                )[:10]
                logger.warning(
                    f"[ClienteAutocomplete] Clientes disponibles en empresa: {list(todos)}"
                )
        else:
            # Sin término de búsqueda: no devolver resultados (Select2 con minimum-input-length)
            logger.info("[ClienteAutocomplete] Sin término de búsqueda, retornando queryset vacío")
            return Cliente.objects.none()

        return qs

    def get_result_label(self, result):
        """
        Formato personalizado para mostrar en el dropdown
        Muestra: "Nombre Apellido - Email (Teléfono)"
        """
        label_parts = []

        # Nombre completo
        if result.apellido:
            label_parts.append(f"{result.nombre} {result.apellido}")
        else:
            label_parts.append(result.nombre)

        # Email si existe
        if result.email:
            label_parts.append(f"- {result.email}")

        # Teléfono si existe
        if result.telefono:
            label_parts.append(f"({result.telefono})")

        return " ".join(label_parts)

    def get_result_value(self, result):
        """Valor que se guarda en el formulario (ID del cliente)"""
        return result.pk


# Vista alternativa más simple para casos específicos
class ClienteSimpleAutocomplete(autocomplete.Select2QuerySetView):
    """
    Autocompletado simple solo por nombre y apellido
    Para casos donde no necesitas búsqueda compleja
    """

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Cliente.objects.none()

        empresa = getattr(self.request.user, "empresa", None)
        if not empresa:
            return Cliente.objects.none()

        qs = Cliente.objects.filter(empresa=empresa).order_by("nombre", "apellido")

        if self.q:
            qs = qs.filter(Q(nombre__icontains=self.q) | Q(apellido__icontains=self.q))

        return qs


def _get_country_from_request(request):
    """Helper para detectar país desde request"""
    empresa = getattr(request.user, "empresa", None)
    raw = getattr(empresa, "pais", None) if empresa else None

    if not raw:
        raw = getattr(request, "country", None)

    if not raw:
        path = (request.path or "").lower()
        if path.startswith("/us/"):
            raw = "US"
        elif path.startswith("/cl/"):
            raw = "CL"
        elif path.startswith("/mx/"):
            raw = "MX"

    country = str(raw or "CL").strip().upper()
    if country in ("US", "USA"):
        return "US"
    if country in ("MX", "MEX"):
        return "MX"
    return "CL"


class MotorAutocomplete(autocomplete.Select2ListView):
    """
    Autocompletado para motores con soporte de tags (creación al vuelo)
    Filtrado por país y modelo (si se proporciona)
    """

    def get_list(self):
        """Lista mixta: catálogo global eGarage + motores privados de la empresa."""
        if not self.request.user.is_authenticated:
            return []

        country = _get_country_from_request(self.request)
        empresa = getattr(self.request.user, "empresa", None)
        global_qs = MotorVehiculo.objects.filter(country=country)

        modelo_id = self.forwarded.get("modelo") or self.request.GET.get("modelo_id")
        modelo = None
        if modelo_id:
            try:
                modelo = Modelo.objects.get(pk=modelo_id, country=country)
                global_qs = global_qs.filter(modelos=modelo)
            except Modelo.DoesNotExist:
                global_qs = MotorVehiculo.objects.none()

        if self.q:
            global_qs = global_qs.filter(nombre__icontains=self.q)

        results = [(str(obj.pk), obj.nombre) for obj in global_qs.order_by("nombre")]

        if empresa and modelo:
            private_qs = MotorVehiculoEmpresa.objects.filter(
                empresa=empresa,
                modelo=modelo,
                country=country,
            )
            if self.q:
                private_qs = private_qs.filter(nombre__icontains=self.q)
            results.extend(
                (f"empresa:{obj.pk}", obj.nombre)
                for obj in private_qs.order_by("nombre")
            )

        return results


class CajaAutocomplete(autocomplete.Select2ListView):
    """
    Autocompletado para cajas con soporte de tags (creación al vuelo)
    Filtrado por país y modelo (si se proporciona)
    """

    def get_list(self):
        """Lista mixta: catálogo global eGarage + cajas privadas de la empresa."""
        if not self.request.user.is_authenticated:
            return []

        country = _get_country_from_request(self.request)
        empresa = getattr(self.request.user, "empresa", None)
        global_qs = CajaVehiculo.objects.filter(country=country)

        modelo_id = self.forwarded.get("modelo") or self.request.GET.get("modelo_id")
        modelo = None
        if modelo_id:
            try:
                modelo = Modelo.objects.get(pk=modelo_id, country=country)
                global_qs = global_qs.filter(modelos=modelo)
            except Modelo.DoesNotExist:
                global_qs = CajaVehiculo.objects.none()

        if self.q:
            global_qs = global_qs.filter(nombre__icontains=self.q)

        results = [(str(obj.pk), obj.nombre) for obj in global_qs.order_by("nombre")]

        if empresa and modelo:
            private_qs = CajaVehiculoEmpresa.objects.filter(
                empresa=empresa,
                modelo=modelo,
                country=country,
            )
            if self.q:
                private_qs = private_qs.filter(nombre__icontains=self.q)
            results.extend(
                (f"empresa:{obj.pk}", obj.nombre)
                for obj in private_qs.order_by("nombre")
            )

        return results
