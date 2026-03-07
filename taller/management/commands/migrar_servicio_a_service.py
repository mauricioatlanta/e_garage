from django.core.management.base import BaseCommand
from django.db import transaction
from django.apps import apps


class Command(BaseCommand):
    help = "Migra Servicio (legacy) -> Service (nuevo) usando codigo_interno como code (fallback LEGACY-{id})."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Rollback intencional.")
        parser.add_argument("--country", default="", help="CL/US. Vacío = todos.")
        parser.add_argument("--limit", type=int, default=0, help="Limitar cantidad (debug).")

    def handle(self, *args, **opts):
        dry = bool(opts["dry_run"])
        country = (opts["country"] or "").upper().strip()
        limit = int(opts["limit"] or 0)

        Servicio = apps.get_model("taller", "Servicio")
        Service = apps.get_model("taller", "Service")

        ServiceI18N = _get_optional("taller", "ServiceI18N")
        ServicePrice = _get_optional("taller", "ServicePrice")
        ServicioName = _get_optional("taller", "ServicioName")

        qs = Servicio.objects.all().select_related("empresa", "categoria")
        if country:
            qs = qs.filter(categoria__country=country)

        total = qs.count()
        if limit:
            qs = qs.order_by("id")[:limit]

        self.stdout.write(
            f"Servicio legacy encontrados: {total}" + (f" (country={country})" if country else "")
        )
        self.stdout.write(
            f"ServiceI18N existe? {bool(ServiceI18N)} | ServicePrice existe? {bool(ServicePrice)} | ServicioName existe? {bool(ServicioName)}"
        )

        created = 0
        updated = 0
        i18n_created = 0
        price_created = 0

        ctx = transaction.atomic() if not dry else _nullcontext()
        with ctx:
            for s in qs.iterator(chunk_size=500):
                empresa = s.empresa
                categoria = s.categoria

                code = (getattr(s, "codigo_interno", None) or "").strip()
                if not code:
                    code = f"LEGACY-{s.id}"

                obj = Service.objects.filter(empresa=empresa, code=code).first()
                if obj:
                    updated += 1
                    _sync_fields(obj, s, categoria, dry=dry)
                else:
                    created += 1
                    if not dry:
                        obj = Service.objects.create(
                            empresa=empresa,
                            code=code,
                            category=_category_to_str(categoria),  # ✅ CharField
                            active=getattr(s, "activo", True),
                            std_hours=_to_std_hours(s),
                        )

                if not dry and obj and ServiceI18N:
                    i18n_created += _ensure_i18n(ServiceI18N, ServicioName, s, obj)

                if not dry and obj and ServicePrice:
                    price_created += _ensure_price(ServicePrice, s, obj)

            if dry:
                self.stdout.write(self.style.WARNING("DRY-RUN: rollback intencional"))
                transaction.set_rollback(True)
                return

        self.stdout.write(self.style.SUCCESS("Migración Servicio -> Service OK"))
        self.stdout.write(
            f"created={created} updated={updated} i18n_created={i18n_created} price_created={price_created}"
        )


def _get_optional(app_label, model_name):
    try:
        return apps.get_model(app_label, model_name)
    except Exception:
        return None


def _to_std_hours(legacy):
    """
    Convierte duracion_estimada_min a horas (float/decimal según tu campo).
    Si no existe o es 0, retorna None.
    """
    mins = getattr(legacy, "duracion_estimada_min", None)
    try:
        if mins is None:
            return None
        mins = int(mins)
        if mins <= 0:
            return None
        return mins / 60.0
    except Exception:
        return None


def _category_to_str(legacy_categoria):
    if not legacy_categoria:
        return ""

    # si ya viene string
    if isinstance(legacy_categoria, str):
        return legacy_categoria.strip()

    # intenta campos típicos en orden de preferencia
    for attr in ("slug", "codigo", "code", "key", "nombre", "name"):
        val = getattr(legacy_categoria, attr, None)
        if isinstance(val, str) and val.strip():
            return val.strip()

    # fallback: pk como string (estable)
    pk = getattr(legacy_categoria, "pk", None)
    return str(pk) if pk is not None else str(legacy_categoria)


def _sync_fields(service_obj, legacy_servicio, legacy_categoria, dry=False):
    changed = False

    # ✅ category es CharField → comparar y setear STRING
    if hasattr(service_obj, "category"):
        new_cat = _category_to_str(legacy_categoria)
        if (service_obj.category or "") != new_cat:
            service_obj.category = new_cat
            changed = True

    if hasattr(service_obj, "active"):
        if service_obj.active != legacy_servicio.activo:
            service_obj.active = legacy_servicio.activo
            changed = True

    if hasattr(service_obj, "std_hours"):
        new_hours = _to_std_hours(legacy_servicio)
        if service_obj.std_hours != new_hours:
            service_obj.std_hours = new_hours
            changed = True

    if changed and not dry:
        service_obj.save()


def _ensure_i18n(ServiceI18N, ServicioName, legacy_serv, new_serv):
    created = 0

    f = {x.name for x in ServiceI18N._meta.fields}
    service_fk = "service" if "service" in f else ("servicio" if "servicio" in f else None)
    lang_f = "lang" if "lang" in f else ("language" if "language" in f else None)
    name_f = "name" if "name" in f else ("nombre" if "nombre" in f else None)
    desc_f = (
        "description" if "description" in f else ("descripcion" if "descripcion" in f else None)
    )

    if not (service_fk and lang_f and name_f):
        return 0

    # Copiar desde ServicioName si existe (idiomas)
    if ServicioName:
        snf = {x.name for x in ServicioName._meta.fields}
        sn_fk = "servicio" if "servicio" in snf else ("service" if "service" in snf else None)
        sn_lang = "lang" if "lang" in snf else ("language" if "language" in snf else None)
        sn_name = "nombre" if "nombre" in snf else ("name" if "name" in snf else None)

        if sn_fk and sn_name:
            for row in ServicioName.objects.filter(**{sn_fk: legacy_serv}):
                lang = (getattr(row, sn_lang, None) if sn_lang else None) or "es"
                lang = str(lang).lower().strip() or "es"
                nm = (getattr(row, sn_name, None) or "").strip()
                if not nm:
                    continue

                defaults = {name_f: nm}
                if desc_f:
                    defaults[desc_f] = ""

                _, was_created = ServiceI18N.objects.get_or_create(
                    **{service_fk: new_serv, lang_f: lang},
                    defaults=defaults,
                )
                if was_created:
                    created += 1

            return created

    # fallback (es)
    legacy_name = (getattr(legacy_serv, "nombre", None) or "").strip()
    if legacy_name:
        defaults = {name_f: legacy_name}
        if desc_f:
            defaults[desc_f] = ""

        _, was_created = ServiceI18N.objects.get_or_create(
            **{service_fk: new_serv, lang_f: "es"},
            defaults=defaults,
        )
        if was_created:
            created += 1

    return created


def _ensure_price(ServicePrice, legacy_serv, new_serv):
    legacy_price = getattr(legacy_serv, "precio_base", None)
    if legacy_price is None:
        return 0

    f = {x.name for x in ServicePrice._meta.fields}
    service_fk = "service" if "service" in f else ("servicio" if "servicio" in f else None)
    amount_f = "amount" if "amount" in f else ("precio" if "precio" in f else None)
    currency_f = "currency" if "currency" in f else ("moneda" if "moneda" in f else None)

    if not (service_fk and amount_f):
        return 0

    defaults = {amount_f: legacy_price}
    if currency_f:
        moneda = getattr(getattr(legacy_serv, "empresa", None), "moneda", None) or "CLP"
        defaults[currency_f] = moneda

    ServicePrice.objects.get_or_create(**{service_fk: new_serv}, defaults=defaults)
    return 1


class _nullcontext:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False
