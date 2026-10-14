from taller.models.compatibility import PartApplication
from taller.models.pieza_desarme import PiezaDesarme

class InterchangeSalesService:

    @staticmethod
    def verificar_compatibilidad_venta(pieza_id, cliente_marca, cliente_modelo, cliente_anio=None):
        """
        Verifica si una pieza física de la yarda (de cualquier origen) 
        es compatible con el vehículo del cliente según el motor canónico.
        """
        try:
            pieza = PiezaDesarme.objects.select_related('vehiculo_desarme').get(id=pieza_id)
        except PiezaDesarme.DoesNotExist:
            return {"compatible": False, "mensaje": "Pieza no encontrada"}

        # 1. Si la pieza pertenece originalmente al mismo modelo del cliente, hay match directo
        v_orig = pieza.vehiculo_desarme
        orig_marca = v_orig.marca_texto or (v_orig.marca.nombre if v_orig.marca else "")
        orig_modelo = v_orig.modelo_texto or (v_orig.modelo.nombre if v_orig.modelo else "")
        
        if orig_marca.lower() == cliente_marca.lower() and orig_modelo.lower() == cliente_modelo.lower():
            return {
                "compatible": True,
                "tipo_match": "directo",
                "pieza": pieza,
                "mensaje": "La pieza proviene del mismo modelo de vehículo."
            }

        # 2. Si no es directa, consultamos el motor canónico PartApplication
        qs = PartApplication.objects.filter(
            codigo_pieza=pieza.codigo,
            activo=True,
            marca__iexact=cliente_marca,
            modelo__iexact=cliente_modelo
        )

        if cliente_anio:
            from django.db.models import Q
            qs = qs.filter(
                Q(anio_desde__lte=cliente_anio) | Q(anio_desde__isnull=True),
                Q(anio_hasta__gte=cliente_anio) | Q(anio_hasta__isnull=True)
            )

        if qs.exists():
            return {
                "compatible": True,
                "tipo_match": "interchange",
                "pieza": pieza,
                "regla": qs.first(),
                "mensaje": f"Match por Interchange: La pieza es de origen ({orig_marca} {orig_modelo}) pero es compatible con el {cliente_marca} {cliente_modelo}."
            }

        return {
            "compatible": False,
            "pieza": pieza,
            "mensaje": f"Advertencia: No hay registro formal de compatibilidad entre esta pieza ({pieza.codigo}) y el vehículo {cliente_marca} {cliente_modelo}."
        }

    @staticmethod
    def registrar_aprendizaje_venta(pieza, cliente_marca, cliente_modelo, cliente_anio=None):
        """
        Auto-aprender: Si el vendedor confirma una venta cruzada exitosa, 
        registramos automáticamente la regla en PartApplication.
        """
        PartApplication.objects.get_or_create(
            codigo_pieza=pieza.codigo,
            marca=cliente_marca,
            modelo=cliente_modelo,
            defaults={
                'anio_desde': cliente_anio,
                'anio_hasta': cliente_anio,
                'fuente': 'venta_mostrador_exitosa',
                'nivel_confianza': 8,
                'activo': True
            }
        )
