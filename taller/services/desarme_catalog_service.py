from taller.models.catalogo_repuesto_empresa import CatalogoRepuestoEmpresa
from taller.models.pieza_desarme import PiezaDesarme

def crear_piezas_desde_catalogo_empresa(vehiculo, empresa, usuario=None):
    """
    Genera las piezas de un vehículo en desarme basándose estrictamente 
    en el catálogo personalizado y activo del suscriptor.
    """
    items_catalogo = CatalogoRepuestoEmpresa.objects.filter(
        empresa=empresa,
        incluido=True
    ).order_by('orden')

    # Si la empresa aún no tiene piezas en su catálogo, no creamos piezas huérfanas
    if not items_catalogo.exists():
        return []

    piezas = []
    for item in items_catalogo:
        pieza = PiezaDesarme(
            vehiculo_desarme=vehiculo,
            empresa=empresa,
            codigo=f"{item.codigo}-{vehiculo.id}",
            nombre=item.nombre or f"Repuesto {item.codigo}",
            categoria=item.categoria or "MOTOR",
            visual_slot=item.visual_slot or "engine.core",
            precio=item.precio_predeterminado or 0,
            estado_pieza="DISPONIBLE",
            ubicacion_tipo="VEHICULO"
        )
        piezas.append(pieza)

    return PiezaDesarme.objects.bulk_create(piezas)
