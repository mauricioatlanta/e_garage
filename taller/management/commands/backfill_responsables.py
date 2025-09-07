from django.core.management.base import BaseCommand
from django.db import transaction

from taller.models import Documento


class Command(BaseCommand):
    help = "Completa Documento.tecnico_responsable y hereda a líneas sin mecanico (repuesto/servicio/otros)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Muestra lo que haría sin escribir cambios.",
        )

    @transaction.atomic
    def handle(self, *args, **opts):
        dry = opts["dry_run"]
        docs = Documento.objects.all()
        set_responsable = 0
        set_lineas_rep = 0
        set_lineas_srv = 0
        set_lineas_otros = 0

        for d in docs.iterator():
            # 1) Completar tecnico_responsable si falta
            if d.tecnico_responsable_id is None:
                cand = getattr(getattr(d, "created_by", None), "tecnico", None)
                cfg = getattr(getattr(d, "empresa", None), "config", None)
                if cand and getattr(cand, "empresa_id", None) == getattr(
                    d, "empresa_id", None
                ):
                    if not dry:
                        d.tecnico_responsable = cand
                        d.save(update_fields=["tecnico_responsable"])
                    set_responsable += 1
                elif cfg and getattr(cfg, "tecnico_por_defecto_id", None):
                    if not dry:
                        d.tecnico_responsable_id = cfg.tecnico_por_defecto_id
                        d.save(update_fields=["tecnico_responsable"])
                    set_responsable += 1

            # 2) Heredar a líneas vacías (solo si hay responsable)
            if d.tecnico_responsable_id:
                # Repuestos
                if hasattr(d, "lineas_repuesto"):
                    qs = d.lineas_repuesto.filter(mecanico__isnull=True)
                    if not dry:
                        set_lineas_rep += qs.update(
                            mecanico_id=d.tecnico_responsable_id
                        )
                    else:
                        set_lineas_rep += qs.count()

                # Servicios (si existen en esta empresa)
                if hasattr(d, "lineas_servicio"):
                    qs = d.lineas_servicio.filter(mecanico__isnull=True)
                    if not dry:
                        set_lineas_srv += qs.update(
                            mecanico_id=d.tecnico_responsable_id
                        )
                    else:
                        set_lineas_srv += qs.count()

                # Otros servicios (si aplica)
                if hasattr(d, "lineas_otro_servicio"):
                    qs = d.lineas_otro_servicio.filter(mecanico__isnull=True)
                    if not dry:
                        set_lineas_otros += qs.update(
                            mecanico_id=d.tecnico_responsable_id
                        )
                    else:
                        set_lineas_otros += qs.count()

        self.stdout.write(
            self.style.SUCCESS(
                f"Backfill OK. tecnico_responsable seteado en {set_responsable} documentos; "
                f"líneas actualizadas: rep={set_lineas_rep}, srv={set_lineas_srv}, otros={set_lineas_otros} "
                f"{'(dry-run)' if dry else ''}"
            )
        )
