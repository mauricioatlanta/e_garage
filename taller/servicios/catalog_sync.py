from django.conf import settings
from django.db import transaction

from .models import Servicio, ServicioName


def _seed_source_company_id(target_empresa):
    source_company_id = getattr(settings, "SERVICE_CATALOG_MASTER_COMPANY_ID", 1)
    if not source_company_id or (
        target_empresa and getattr(target_empresa, "id", None) == source_company_id
    ):
        return None
    return source_company_id


@transaction.atomic
def ensure_company_seed_services(empresa, country=None):
    """
    Si la empresa no tiene servicios para el país solicitado, clona un catálogo
    mínimo desde la empresa maestra configurada. Mantiene aislamiento multi-tenant
    creando registros propios para la empresa destino.
    """
    if not empresa:
        return 0

    current = Servicio.objects.filter(empresa=empresa, activo=True)
    if country:
        current = current.filter(categoria__country=country)
    if current.exists():
        return 0

    source_company_id = _seed_source_company_id(empresa)
    if not source_company_id:
        return 0

    source_services = (
        Servicio.objects.filter(empresa_id=source_company_id, activo=True)
        .select_related("categoria", "subcategoria", "servicio_base")
        .prefetch_related("names")
        .order_by("categoria__orden", "subcategoria__orden", "nombre")
    )
    if country:
        source_services = source_services.filter(categoria__country=country)

    created = 0
    for source in source_services:
        service, was_created = Servicio.objects.get_or_create(
            empresa=empresa,
            nombre=source.nombre,
            categoria=source.categoria,
            defaults={
                "servicio_base": source.servicio_base,
                "subcategoria": source.subcategoria,
                "descripcion": source.descripcion,
                "precio_base": source.precio_base,
                "duracion_estimada_min": source.duracion_estimada_min,
                "codigo_interno": source.codigo_interno,
                "rubro_sugerido": source.rubro_sugerido,
                "rubro_efectivo": source.rubro_efectivo,
                "activo": source.activo,
            },
        )
        if was_created:
            created += 1

        for name in source.names.all():
            ServicioName.objects.get_or_create(
                servicio=service,
                language=name.language,
                is_default=name.is_default,
                defaults={
                    "label": name.label,
                    "aliases": list(name.aliases or []),
                },
            )

    return created
