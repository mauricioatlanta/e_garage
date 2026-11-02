"""
VehicleStateService — Servicio de transiciones de estado operacional.

Responsabilidades:
- Validar que la transición sea permitida por la matriz.
- Bloquear el vehículo con select_for_update() dentro de transaction.atomic().
- Actualizar VehiculoDesarme.estado_operativo.
- Crear VehiculoDesarmeEvent de tipo ESTADO_OPERATIVO_CAMBIADO.
- Soportar idempotencia cuando se entrega idempotency_key.
- Garantizar aislamiento multi-tenant en cada operación.

Nota: no modifica estado_desarme (campo legacy). Ambos coexisten.
"""

from django.core.exceptions import ValidationError
from django.db import transaction

from taller.models.vehiculo_desarme import EstadoOperativo, VehiculoDesarme
from taller.models.vehiculo_desarme_event import TipoEventoDesarme, VehiculoDesarmeEvent

# Matriz de transiciones permitidas.
# Definida en un único lugar para que sea la fuente de verdad del sistema.
_TRANSITIONS: dict[str, frozenset[str]] = {
    EstadoOperativo.INGRESADO:        frozenset({
        EstadoOperativo.EN_REVISION,
        EstadoOperativo.EN_PROCESAMIENTO,  # flujo admin / directo
    }),
    EstadoOperativo.EN_REVISION:      frozenset({EstadoOperativo.EN_PROCESAMIENTO}),
    EstadoOperativo.EN_PROCESAMIENTO: frozenset({EstadoOperativo.EN_CIERRE}),
    EstadoOperativo.EN_CIERRE:        frozenset({EstadoOperativo.CERRADO}),
    EstadoOperativo.CERRADO:          frozenset(),  # terminal — no hay reapertura en esta fase
}


class TransicionInvalidaError(Exception):
    """El estado objetivo no es alcanzable desde el estado actual."""


class VehicleStateService:
    """
    Servicio de dominio para cambios de estado_operativo en VehiculoDesarme.

    Uso:
        from taller.services.vehicle_state_service import VehicleStateService

        VehicleStateService.transition(
            vehicle=vehiculo,
            target_state=EstadoOperativo.EN_REVISION,
            user=request.user,
            reason="revision_iniciada",
        )
    """

    @classmethod
    def transition(
        cls,
        *,
        vehicle: VehiculoDesarme,
        target_state: str,
        user=None,
        reason: str = "",
        idempotency_key: str | None = None,
    ) -> VehiculoDesarmeEvent:
        """
        Ejecuta una transición de estado_operativo de forma atómica y auditada.

        Args:
            vehicle:          Instancia de VehiculoDesarme a transicionar.
            target_state:     Valor de EstadoOperativo destino.
            user:             Usuario que origina el cambio (puede ser None para procesos).
            reason:           Motivo libre del cambio (se guarda en metadata).
            idempotency_key:  Clave única por tenant. Si ya procesada, devuelve el evento
                              existente sin crear duplicado.

        Returns:
            VehiculoDesarmeEvent creado (o existente si idempotente).

        Raises:
            TransicionInvalidaError: si la transición no está permitida.
            VehiculoDesarme.DoesNotExist: si el vehículo no existe en la empresa.
        """
        empresa = vehicle.empresa

        # Idempotencia: si ya existe un evento con esta clave en el tenant, retornar
        if idempotency_key:
            existing = VehiculoDesarmeEvent.objects.filter(
                empresa=empresa,
                idempotency_key=idempotency_key,
            ).first()
            if existing:
                return existing

        with transaction.atomic():
            # Re-leer con bloqueo dentro de la transacción para evitar race condition
            locked = (
                VehiculoDesarme.objects
                .select_for_update()
                .filter(pk=vehicle.pk, empresa=empresa)
                .first()
            )
            if locked is None:
                raise VehiculoDesarme.DoesNotExist(
                    f"VehiculoDesarme pk={vehicle.pk} no existe para empresa={empresa.pk}"
                )

            current = locked.estado_operativo
            cls._validate_transition(current, target_state)

            # Actualizar el estado
            locked.estado_operativo = target_state
            locked.save(update_fields=["estado_operativo", "updated_at"])

            # Registrar el evento
            event = VehiculoDesarmeEvent.objects.create(
                empresa=empresa,
                vehiculo=locked,
                tipo=TipoEventoDesarme.ESTADO_OPERATIVO_CAMBIADO,
                created_by=user,
                idempotency_key=idempotency_key,
                metadata={
                    "from": current,
                    "to": target_state,
                    "reason": reason,
                },
            )

        return event

    @classmethod
    def _validate_transition(cls, current: str, target: str) -> None:
        """Valida que la transición esté permitida por la matriz."""
        allowed = _TRANSITIONS.get(current, frozenset())
        if target not in allowed:
            if not allowed:
                msg = f"El estado '{current}' es terminal. No se permiten transiciones."
            else:
                allowed_str = ", ".join(sorted(allowed))
                msg = (
                    f"Transición '{current}' → '{target}' no permitida. "
                    f"Desde '{current}' se puede ir a: {allowed_str}."
                )
            raise TransicionInvalidaError(msg)

    @classmethod
    def allowed_transitions(cls, current: str) -> frozenset[str]:
        """Devuelve los estados a los que puede transicionar current."""
        return _TRANSITIONS.get(current, frozenset())
