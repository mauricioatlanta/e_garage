from django.core.management.base import BaseCommand
from django.db.models import Count, Q

from taller.models.pieza_desarme import PiezaDesarme, ESTADO_DISPONIBLE


class Command(BaseCommand):
    help = "Diagnostica el campo publicada en PiezaDesarme — valida backfill y detecta inconsistencias."

    def handle(self, *args, **options):
        total = PiezaDesarme.objects.count()
        publicadas = PiezaDesarme.objects.filter(publicada=True).count()
        no_publicadas = PiezaDesarme.objects.filter(publicada=False).count()

        self.stdout.write(f"\n{'─'*50}")
        self.stdout.write(f"  DIAGNÓSTICO: campo publicada — PiezaDesarme")
        self.stdout.write(f"{'─'*50}")
        self.stdout.write(f"  Total piezas:        {total:>8,}")
        self.stdout.write(f"  publicada=True:      {publicadas:>8,}")
        self.stdout.write(f"  publicada=False:     {no_publicadas:>8,}")

        # Caso problemático: activo=True, DISPONIBLE, publicada=False → backfill no se aplicó
        sin_publicar_activas = PiezaDesarme.objects.filter(
            activo=True,
            estado_pieza=ESTADO_DISPONIBLE,
            publicada=False,
        ).count()

        self.stdout.write(f"\n  Activas+DISPONIBLE con publicada=False: {sin_publicar_activas:>5,}")
        if sin_publicar_activas == 0:
            self.stdout.write(self.style.SUCCESS("  ✓ Backfill aplicado correctamente."))
        else:
            self.stdout.write(
                self.style.WARNING(
                    f"  ⚠ {sin_publicar_activas} pieza(s) activas y disponibles no están publicadas.\n"
                    "    Ejecutar: PiezaDesarme.objects.filter(activo=True, estado_pieza='DISPONIBLE').update(publicada=True)"
                )
            )

        # Invariante: activo=False no debería tener publicada=True
        inactivas_publicadas = PiezaDesarme.objects.filter(
            activo=False,
            publicada=True,
        ).count()

        if inactivas_publicadas:
            self.stdout.write(
                self.style.ERROR(
                    f"\n  ✗ {inactivas_publicadas} pieza(s) con activo=False tienen publicada=True."
                    " Invariante violado: activo=False implica publicada=False."
                )
            )
        else:
            self.stdout.write(self.style.SUCCESS("  ✓ Invariante activo→publicada consistente."))

        # Desglose por empresa (top 10 con piezas publicadas)
        por_empresa = (
            PiezaDesarme.objects.filter(publicada=True)
            .values("empresa__nombre_empresa")
            .annotate(total=Count("id"))
            .order_by("-total")[:10]
        )
        if por_empresa:
            self.stdout.write(f"\n  Top empresas con piezas publicadas:")
            for row in por_empresa:
                self.stdout.write(f"    {row['empresa__nombre_empresa']:<35} {row['total']:>6,}")

        self.stdout.write(f"{'─'*50}\n")
