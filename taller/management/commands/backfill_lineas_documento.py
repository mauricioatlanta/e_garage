import json
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from taller.models import (
    Documento,
    LineaOtroServicio,
    LineaRepuesto,
    LineaServicio,
    Repuesto,
)


class Command(BaseCommand):
    help = "Reconstruye líneas de documentos legacy desde documento.detalles. Soporta --dry-run."

    def add_arguments(self, parser):
        parser.add_argument(
            "--ids", nargs="*", type=int, help="IDs de documentos a procesar"
        )
        parser.add_argument(
            "--dry-run", action="store_true", help="No escribir cambios"
        )

    def handle(self, *args, **opts):
        ids = opts.get("ids")
        qs = Documento.objects.all()
        if ids:
            qs = qs.filter(id__in=ids)

        procesados = creadas = 0
        for doc in qs.iterator():
            rep_c = doc.lineas_repuesto.count()
            ser_c = doc.lineas_servicio.count()
            otr_c = doc.lineas_otro_servicio.count()
            if rep_c or ser_c or otr_c:
                continue  # ya tiene líneas

            # Buscar datos en varios campos posibles
            detalles_raw = (
                getattr(doc, "detalles", None)
                or getattr(doc, "json_data", None)
                or getattr(doc, "data_payload", None)
                or getattr(doc, "items_data", None)
            )

            if not detalles_raw:
                # También buscar en DetalleDocumento si existe
                try:
                    detalles_count = doc.detalles.count()
                    if detalles_count > 0:
                        self.stdout.write(
                            self.style.NOTICE(
                                f"[INFO] Doc {doc.id} tiene {detalles_count} DetalleDocumento pero no JSON detalles"
                            )
                        )
                except:
                    pass

                self.stdout.write(
                    self.style.WARNING(
                        f"[SKIP] Doc {doc.id} sin datos de 'detalles' o campos relacionados"
                    )
                )
                continue

            try:
                detalles = (
                    detalles_raw
                    if isinstance(detalles_raw, dict)
                    else json.loads(detalles_raw)
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"[ERR] Doc {doc.id} JSON inválido: {e}")
                )
                continue

            repuestos = detalles.get("repuestos", []) or detalles.get(
                "lineas_repuesto", []
            )
            servicios = detalles.get("servicios", []) or detalles.get(
                "lineas_servicio", []
            )
            otros = detalles.get("otros", []) or detalles.get(
                "lineas_otro_servicio", []
            )

            if opts["dry_run"]:
                self.stdout.write(
                    self.style.NOTICE(
                        f"[DRY] Doc {doc.id} crear rep:{len(repuestos)} ser:{len(servicios)} otr:{len(otros)}"
                    )
                )
                procesados += 1
                creadas += len(repuestos) + len(servicios) + len(otros)
                continue

            with transaction.atomic():
                # Repuestos
                for r in repuestos:
                    rep_id = r.get("id")
                    if not rep_id and r.get("part_number"):
                        rep = Repuesto.objects.filter(
                            part_number__iexact=r["part_number"]
                        ).first()
                        rep_id = rep.id if rep else None
                    LineaRepuesto.objects.create(
                        documento=doc,
                        repuesto_id=rep_id,
                        nombre=r.get("nombre") or r.get("descripcion", ""),
                        cantidad=Decimal(str(r.get("cantidad", 1))),
                        precio_unitario=Decimal(
                            str(r.get("precio", r.get("precio_unitario", 0)))
                        ),
                        descuento=Decimal(str(r.get("descuento", 0))),
                    )
                # Servicios
                for s in servicios:
                    LineaServicio.objects.create(
                        documento=doc,
                        codigo=s.get("codigo", ""),
                        nombre=s.get("nombre") or s.get("descripcion", ""),
                        cantidad=Decimal(str(s.get("cantidad", 1))),
                        precio_unitario=Decimal(
                            str(s.get("precio", s.get("precio_unitario", 0)))
                        ),
                        descuento=Decimal(str(s.get("descuento", 0))),
                    )
                # Otros
                for o in otros:
                    precio = Decimal(str(o.get("precio_cliente", o.get("precio", 0))))
                    costo = Decimal(str(o.get("costo_interno", o.get("costo", 0))))
                    LineaOtroServicio.objects.create(
                        documento=doc,
                        nombre=o.get("nombre") or o.get("descripcion", ""),
                        empresa_externa=o.get("empresa_externa", ""),
                        cantidad=Decimal(str(o.get("cantidad", 1))),
                        costo_interno=costo,
                        precio_cliente=precio,
                        ganancia=precio - costo,
                    )
            procesados += 1
            creadas += len(repuestos) + len(servicios) + len(otros)
            self.stdout.write(
                self.style.SUCCESS(
                    f"[OK] Doc {doc.id} líneas creadas: rep:{len(repuestos)} ser:{len(servicios)} otr:{len(otros)}"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(f"Procesados: {procesados}, líneas creadas: {creadas}")
        )
