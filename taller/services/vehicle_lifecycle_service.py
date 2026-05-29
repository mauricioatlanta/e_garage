from taller.models.vehiculos import Vehiculo
from taller.services.desarme_financial_service import calcular_estado_financiero


class VehicleLifecycleService:
    """Servicio para mantener el estado financiero/lifecycle de vehículos de desarme."""

    @classmethod
    def update_lifecycle(cls, vehiculo: Vehiculo) -> Vehiculo:
        nuevo_estado = calcular_estado_financiero(vehiculo)
        if vehiculo.estado_desarme != nuevo_estado:
            vehiculo.estado_desarme = nuevo_estado
            vehiculo.save(update_fields=["estado_desarme"])
        return vehiculo

    @classmethod
    def update_lifecycle_for_documento(cls, documento):
        vehiculos = Vehiculo.objects.filter(
            piezas_desarme__lineas_repuesto__documento=documento,
            piezas_desarme__lineas_repuesto__origen_repuesto="DESARME",
        ).distinct()
        updated = []
        for vehiculo in vehiculos:
            updated.append(cls.update_lifecycle(vehiculo))
        return updated
