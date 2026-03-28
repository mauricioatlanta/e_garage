from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


class Command(BaseCommand):
    help = (
        "Convierte precios de piezas de desarme a USD (2 decimales) usando una tasa CLP→USD.\n"
        "Uso recomendado: --dry-run primero."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--rate",
            type=str,
            required=True,
            help="Tasa CLP→USD (ej: 950.0). USD = CLP / rate",
        )
        parser.add_argument(
            "--empresa-id",
            type=int,
            default=None,
            help="Limitar a una empresa específica.",
        )
        parser.add_argument(
            "--pais",
            type=str,
            default="US",
            help="Limitar por país de empresa (default: US).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="No escribe cambios; solo muestra conteos.",
        )

    def handle(self, *args, **options):
        from taller.models import Empresa
        from taller.models.pieza_desarme import PiezaDesarme

        try:
            rate = Decimal(str(options["rate"]))
        except Exception as e:
            raise CommandError(f"--rate inválida: {e}")
        if rate <= 0:
            raise CommandError("--rate debe ser > 0")

        empresa_id = options.get("empresa_id")
        pais = (options.get("pais") or "").strip().upper()
        dry_run = bool(options.get("dry_run"))

        empresas_qs = Empresa.objects.all()
        if pais:
            empresas_qs = empresas_qs.filter(pais__iexact=pais)
        if empresa_id:
            empresas_qs = empresas_qs.filter(pk=empresa_id)

        empresa_ids = list(empresas_qs.values_list("id", flat=True))
        if not empresa_ids:
            self.stdout.write(self.style.WARNING("No hay empresas que coincidan con filtros."))
            return

        qs = PiezaDesarme.objects.filter(empresa_id__in=empresa_ids)

        fields = [
            "precio_venta_sugerido",
            "precio_referencia",
            "precio_sugerido",
            "costo_asignado",
        ]

        def to_usd(v: Decimal | None) -> Decimal | None:
            if v is None:
                return None
            if v == 0:
                return Decimal("0.00")
            usd = (v / rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            return usd

        touched = 0
        changed = 0

        with transaction.atomic():
            for pieza in qs.iterator(chunk_size=500):
                touched += 1
                updates = {}
                for f in fields:
                    cur = getattr(pieza, f, None)
                    if cur is None:
                        continue
                    new = to_usd(cur)
                    if new != cur:
                        updates[f] = new

                if updates:
                    changed += 1
                    if not dry_run:
                        for k, v in updates.items():
                            setattr(pieza, k, v)
                        pieza.save(update_fields=list(updates.keys()))

            if dry_run:
                transaction.set_rollback(True)

        self.stdout.write(
            self.style.SUCCESS(
                f"OK. Piezas revisadas: {touched}. Piezas con cambios: {changed}. "
                f"{'DRY-RUN (sin escribir)' if dry_run else 'Cambios aplicados'}."
            )
        )
